from rest_framework.exceptions import ValidationError


class ResultStatusResolver:
    @classmethod
    def resolve(cls, status_name: str, project_id: int):
        from django.db.models import Q
        from testy.tests_representation.models import ResultStatus

        status = ResultStatus.objects.filter(
            Q(project_id=project_id) | Q(project_id__isnull=True),
            name__iexact=status_name,
            is_deleted=False,
        ).first()
        if not status:
            raise ValidationError(f'Status "{status_name}" not found in this project.')
        return status
