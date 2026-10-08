from django.db import transaction
from rest_framework.exceptions import ValidationError


class SoftDeletion:
    @staticmethod
    @transaction.atomic
    def delete(view, instance):
        from testy.root.querysets import SoftDeleteQuerySet
        from testy.tests_description.models import TestSuite
        from testy.tests_description.services.suites import TestSuiteService

        view.action = "destroy"
        view.get_object = lambda: instance
        metadata, _ = view.get_deleted_objects()
        querysets = [view._get_qs_from_meta_data(item, SoftDeleteQuerySet) for item in metadata]
        for queryset in querysets:
            if (
                hasattr(queryset.model, "project")
                and queryset.exclude(project_id=instance.project_id).exists()
            ):
                raise ValidationError("Invalid project relationship.")
        for queryset in querysets:
            if queryset.model == TestSuite:
                TestSuiteService.unlink_custom_attributes(queryset)
            queryset.delete()
