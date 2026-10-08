from testy_mcp.services.access_control import AccessControl


class CaseLabels:
    @classmethod
    def attach(cls, case, label_ids: list[int]):
        """Attach labels to a test case via GenericForeignKey."""
        from django.contrib.contenttypes.models import ContentType
        from testy.core.models import LabeledItem

        AccessControl().related_many("label", label_ids, case.project_id)
        ct = ContentType.objects.get_for_model(case)
        for label_id in label_ids:
            LabeledItem.objects.create(label_id=label_id, content_type=ct, object_id=case.id)

    @classmethod
    def sync(cls, case, label_ids: list[int]):
        """Replace labels on a test case."""
        from django.contrib.contenttypes.models import ContentType
        from testy.core.models import LabeledItem

        AccessControl().related_many("label", label_ids, case.project_id)
        ct = ContentType.objects.get_for_model(case)
        LabeledItem.objects.filter(content_type=ct, object_id=case.id).delete()
        for label_id in label_ids:
            LabeledItem.objects.create(label_id=label_id, content_type=ct, object_id=case.id)
