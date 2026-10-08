from types import SimpleNamespace

from django.db.models import Exists, OuterRef, Q
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from testy_mcp.context import RequestContext


class ProjectAccess:
    def __init__(self):
        self.user = RequestContext.get()
        if self.user is None or not self.user.is_authenticated:
            raise NotAuthenticated()

    def queryset(self):
        from testy.core.selectors.projects import ProjectSelector

        return ProjectSelector(self.user).project_list().distinct()

    def readable(self):
        from testy.users.choices import UserAllowedPermissionCodenames
        from testy.users.models import Membership
        from testy.users.selectors.roles import RoleSelector

        queryset = self.queryset()
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

    def get(self, project_id: int):
        from rest_framework.generics import get_object_or_404
        from testy.core.permissions import ProjectRetrievePermission

        project = get_object_or_404(
            self.queryset().select_related("projectstatistics"), pk=project_id
        )
        request = SimpleNamespace(user=self.user)
        view = SimpleNamespace(action="retrieve")
        if not ProjectRetrievePermission().has_object_permission(request, view, project):
            raise PermissionDenied()
        return project
