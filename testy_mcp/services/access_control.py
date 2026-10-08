from importlib import import_module
from types import SimpleNamespace

from django.db.models import Exists, F, OuterRef, Q
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, ValidationError

from testy_mcp.context import RequestContext


class AccessControl:
    entities = {
        "project": ("testy.core.api.v2.views", "ProjectViewSet"),
        "label": ("testy.core.api.v2.views", "LabelViewSet"),
        "suite": ("testy.tests_description.api.v2.views", "TestSuiteViewSet"),
        "case": ("testy.tests_description.api.v2.views", "TestCaseViewSet"),
        "plan": ("testy.tests_representation.api.v2.views", "TestPlanViewSet"),
        "test": ("testy.tests_representation.api.v2.views", "TestViewSet"),
        "result": ("testy.tests_representation.api.v2.views", "TestResultViewSet"),
        "status": ("testy.tests_representation.api.v2.views", "ResultStatusViewSet"),
    }
    methods = {
        "list": "GET",
        "retrieve": "GET",
        "create": "POST",
        "update": "PUT",
        "destroy": "DELETE",
    }

    def __init__(self):
        self.user = RequestContext.get()
        if self.user is None or not self.user.is_authenticated or not self.user.is_active:
            raise NotAuthenticated()

    def _view(self, entity):
        module, name = self.entities[entity]
        return getattr(import_module(module), name)()

    def _queryset(self, entity):
        model = self._view(entity).queryset.model
        return model.objects.filter(is_deleted=False)

    @staticmethod
    def _find(queryset, **filters):
        from rest_framework.generics import get_object_or_404

        return get_object_or_404(queryset, **filters)

    def _check(self, entity, action, project_id=None, instance=None, data=None):
        self.require_scope(action)
        view = self._view(entity)
        view.action = action
        view.request = SimpleNamespace(
            user=self.user,
            method=self.methods[action],
            data=data if data is not None else {"project": project_id},
            query_params={"project": project_id} if action == "list" else {},
            authenticators=[],
        )
        view.check_permissions(view.request)
        if instance is not None:
            view.check_object_permissions(view.request, instance)

    @staticmethod
    def require_scope(action):
        scopes = RequestContext.scopes()
        if scopes is None:
            return
        operation = "read" if action in {"list", "retrieve"} else "write"
        if not set(scopes) & {operation, f"mcp:{operation}"}:
            raise PermissionDenied(f"OAuth scope {operation} is required.")

    def projects(self):
        from testy.core.selectors.projects import ProjectSelector
        from testy.users.choices import UserAllowedPermissionCodenames
        from testy.users.models import Membership
        from testy.users.selectors.roles import RoleSelector

        self._check("project", "list")
        queryset = ProjectSelector(self.user).project_list().distinct()
        if self.user.is_superuser:
            return queryset
        permitted = Membership.objects.filter(
            user=self.user,
            project=OuterRef("pk"),
            role__permissions__codename=UserAllowedPermissionCodenames.VIEW_PROJECT,
        )
        queryset = queryset.alias(_mcp_can_view=Exists(permitted))
        condition = Q(_mcp_can_view=True)
        if not RoleSelector.restricted_project_access(self.user):
            condition |= Q(is_private=False)
        return queryset.filter(condition)

    def get(self, entity, object_id, action="retrieve"):
        self.require_scope(action)
        queryset = self._queryset(entity)
        if entity == "project":
            from testy.core.selectors.projects import ProjectSelector

            queryset = (
                ProjectSelector(self.user)
                .project_list()
                .distinct()
                .select_related("projectstatistics")
            )
        else:
            queryset = queryset.select_related("project").filter(project__is_deleted=False)
        instance = self._find(queryset, pk=object_id)
        project_id = instance.pk if entity == "project" else instance.project_id
        self._check(entity, action, project_id, instance, data={})
        self.validate_queryset(entity, queryset.filter(pk=instance.pk))
        return instance

    def list(self, entity, project_id):
        self.require_scope("list")
        project = self._find(self._queryset("project"), pk=project_id)
        self._check("project", "retrieve", project_id, project)
        self._check(entity, "list", project_id)
        queryset = self._queryset(entity)
        if entity == "status":
            queryset = queryset.filter(Q(project_id=project_id) | Q(project_id__isnull=True))
        else:
            queryset = queryset.filter(project_id=project_id)
        return self.validate_queryset(entity, queryset)

    def create(self, entity, project_id, data=None):
        self.require_scope("create")
        project = self._find(self._queryset("project"), pk=project_id)
        self._check(entity, "create", project_id, data={"project": project_id, **(data or {})})
        return project

    def plan_for_tests(self, plan_id):
        self.require_scope("create")
        plan = self._find(
            self._queryset("plan").select_related("project"),
            pk=plan_id,
            project__is_deleted=False,
        )
        self.create("test", plan.project_id, {"plan": plan.pk})
        self.validate_queryset("plan", self._queryset("plan").filter(pk=plan.pk))
        return plan

    def delete(self, entity, object_id):
        from testy_mcp.services.soft_deletion import SoftDeletion

        instance = self.get(entity, object_id, "destroy")
        SoftDeletion.delete(self._view(entity), instance)

    def related(self, entity, object_id, project_id):
        return self._find(self.related_many(entity, [object_id], project_id), pk=object_id)

    def related_many(self, entity, object_ids, project_id):
        queryset = self._queryset(entity).filter(pk__in=object_ids, project_id=project_id)
        if set(queryset.values_list("pk", flat=True)) != set(object_ids):
            from rest_framework.exceptions import NotFound

            raise NotFound("Related objects were not found in this project.")
        return self.validate_queryset(entity, queryset)

    def parent(self, entity, parent_id, project_id, instance=None):
        from testy.core.validators import RecursionValidator

        parent = self.related(entity, parent_id, project_id)
        RecursionValidator(type(parent))({"parent": parent}, SimpleNamespace(instance=instance))
        if entity == "plan":
            from testy.tests_representation.validators import TestPlanParentValidator

            TestPlanParentValidator()({"parent": parent})
        return parent

    def plan_cases(self, case_ids, project_id):
        from testy.tests_representation.validators import TestPlanCasesValidator

        cases = self.related_many("case", case_ids, project_id)
        TestPlanCasesValidator()({"test_cases": case_ids})
        return cases

    def submit(self, test):
        from testy.tests_representation.validators import TestResultArchiveTestValidator

        self.validate_queryset("test", self._queryset("test").filter(pk=test.pk))
        self.create("result", test.project_id, {"test": test.pk})
        TestResultArchiveTestValidator()({"test": test}, SimpleNamespace(instance=None))

    def test_for_result(self, test_id):
        self.require_scope("create")
        test = self._find(
            self._queryset("test").select_related("project", "case", "plan"),
            pk=test_id,
            project__is_deleted=False,
        )
        self.submit(test)
        return test

    def plan_for_results(self, plan_id):
        self.require_scope("create")
        plan = self._find(
            self._queryset("plan").select_related("project"),
            pk=plan_id,
            project__is_deleted=False,
        )
        first_test = self._queryset("test").filter(plan_id=plan.pk).first()
        if first_test is None:
            raise ValidationError("No tests in this plan.")
        self.create("result", plan.project_id, {"test": first_test.pk})
        queryset = self._queryset("test").filter(plan_id=plan.pk, project_id=plan.project_id)
        self.validate_queryset("plan", self._queryset("plan").filter(pk=plan.pk))
        if (
            self._queryset("test")
            .filter(plan_id=plan.pk)
            .exclude(project_id=plan.project_id)
            .exists()
        ):
            raise ValidationError("Invalid project relationship.")
        return plan, self.validate_queryset("test", queryset).select_related(
            "case", "plan", "project"
        )

    def tests(self, plan):
        return self.list("test", plan.project_id).filter(plan_id=plan.pk)

    def case_payload(self, data, project_id):
        if not isinstance(data, dict) or not isinstance(data.get("name"), str):
            raise ValidationError("Each case must have a name.")
        if data.get("label_ids"):
            self.related_many("label", data["label_ids"], project_id)

    def results(self, test):
        queryset = self._queryset("result").filter(test_id=test.pk)
        return self.validate_queryset("result", queryset)

    def case_labels(self, project_id, case_ids):
        from django.contrib.contenttypes.models import ContentType
        from testy.core.models import LabeledItem

        model = self._queryset("case").model
        queryset = LabeledItem.objects.filter(
            content_type=ContentType.objects.get_for_model(model),
            object_id__in=case_ids,
            is_deleted=False,
            label__is_deleted=False,
        ).select_related("label")
        if queryset.exclude(label__project_id=project_id).exists():
            raise ValidationError("Invalid project relationship.")
        return queryset

    def case_steps(self, case):
        queryset = case.steps.filter(is_deleted=False)
        if queryset.exclude(project_id=case.project_id).exists():
            raise ValidationError("Invalid project relationship.")
        return queryset

    def case_steps_many(self, cases):
        self.require_scope("retrieve")
        case_projects = {case.pk: case.project_id for case in cases if case.is_steps}
        if not case_projects:
            return []

        from testy.tests_description.models import TestCaseStep

        steps = list(
            TestCaseStep.objects.filter(test_case_id__in=case_projects, is_deleted=False).order_by(
                "test_case_id", "sort_order", "id"
            )
        )
        if any(step.project_id != case_projects[step.test_case_id] for step in steps):
            raise ValidationError("Invalid project relationship.")
        return steps

    @staticmethod
    def validate_queryset(entity, queryset):
        invalid = Q()
        if entity in {"suite", "plan"}:
            invalid = Q(parent__isnull=False) & (
                ~Q(parent__project_id=F("project_id")) | Q(parent__is_deleted=True)
            )
        elif entity == "case":
            invalid = ~Q(suite__project_id=F("project_id")) | Q(suite__is_deleted=True)
        elif entity == "test":
            invalid = (
                ~Q(case__project_id=F("project_id"))
                | ~Q(plan__project_id=F("project_id"))
                | ~Q(case__suite__project_id=F("project_id"))
                | Q(case__is_deleted=True)
                | Q(case__suite__is_deleted=True)
                | Q(plan__is_deleted=True)
                | (
                    Q(last_status__project_id__isnull=False)
                    & ~Q(last_status__project_id=F("project_id"))
                )
            )
        elif entity == "result":
            invalid = (
                ~Q(test__project_id=F("project_id"))
                | ~Q(test__case__project_id=F("project_id"))
                | ~Q(test__plan__project_id=F("project_id"))
                | Q(test__is_deleted=True)
                | (Q(status__project_id__isnull=False) & ~Q(status__project_id=F("project_id")))
            )
        if invalid and queryset.filter(invalid).exists():
            raise ValidationError("Invalid project relationship.")
        return queryset
