import logging

from django.db import transaction
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger('testy_mcp')

MAX_BULK_CASES = 100


def _attach_labels(case, label_ids: list[int]):
    """Attach labels to a test case via GenericForeignKey."""
    from testy.core.models import LabeledItem
    from django.contrib.contenttypes.models import ContentType

    ct = ContentType.objects.get_for_model(case)
    for label_id in label_ids:
        LabeledItem.objects.create(
            label_id=label_id,
            content_type=ct,
            object_id=case.id,
        )


def _sync_labels(case, label_ids: list[int]):
    """Replace labels on a test case."""
    from testy.core.models import LabeledItem
    from django.contrib.contenttypes.models import ContentType

    ct = ContentType.objects.get_for_model(case)
    LabeledItem.objects.filter(content_type=ct, object_id=case.id).delete()
    for label_id in label_ids:
        LabeledItem.objects.create(
            label_id=label_id,
            content_type=ct,
            object_id=case.id,
        )


def register(mcp: FastMCP):

    @mcp.tool()
    def list_cases(
        project_id: int,
        suite_id: int | None = None,
        search: str = '',
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List test cases with filtering and pagination.

        Args:
            project_id: Project ID
            suite_id: Filter by suite
            search: Search by case name
            limit: Max records to return (default: 50)
            offset: Pagination offset
        """
        from testy.tests_description.models import TestCase
        from testy.core.models import LabeledItem
        from django.contrib.contenttypes.models import ContentType

        qs = TestCase.objects.filter(project_id=project_id, is_deleted=False)
        if suite_id:
            qs = qs.filter(suite_id=suite_id)
        if search:
            qs = qs.filter(name__icontains=search)

        total = qs.count()
        cases = list(qs.select_related('suite')[offset:offset + limit])

        ct = ContentType.objects.get_for_model(TestCase)
        case_ids = [c.id for c in cases]
        labeled = (
            LabeledItem.objects
            .filter(content_type=ct, object_id__in=case_ids, is_deleted=False)
            .select_related('label')
        )
        labels_by_case = {}
        for li in labeled:
            labels_by_case.setdefault(li.object_id, []).append(
                {'id': li.label_id, 'name': li.label.name}
            )

        return {
            'total': total,
            'limit': limit,
            'offset': offset,
            'cases': [
                {
                    'id': c.id,
                    'name': c.name,
                    'suite_id': c.suite_id,
                    'suite_name': c.suite.name,
                    'is_steps': c.is_steps,
                    'estimate': c.estimate,
                    'labels': labels_by_case.get(c.id, []),
                }
                for c in cases
            ],
        }

    @mcp.tool()
    def get_case(case_id: int) -> dict:
        """Get full test case content.

        Args:
            case_id: Test case ID
        """
        from testy.tests_description.models import TestCase

        c = TestCase.objects.select_related('suite').get(id=case_id, is_deleted=False)

        labels = []
        for li in c.labeled_items.select_related('label').all():
            if hasattr(li, 'label') and li.label:
                labels.append({'id': li.label.id, 'name': li.label.name})

        steps = []
        if c.is_steps:
            steps = [
                {'id': s.id, 'name': s.name, 'scenario': s.scenario, 'expected': s.expected, 'sort_order': s.sort_order}
                for s in c.steps.filter(is_deleted=False).order_by('sort_order', 'id')
            ]

        return {
            'id': c.id,
            'name': c.name,
            'suite': {'id': c.suite_id, 'name': c.suite.name},
            'setup': c.setup,
            'scenario': c.scenario,
            'expected': c.expected,
            'teardown': c.teardown,
            'description': c.description,
            'estimate': c.estimate,
            'is_steps': c.is_steps,
            'labels': labels,
            'steps': steps,
            'created_at': c.created_at.isoformat() if c.created_at else None,
            'updated_at': c.updated_at.isoformat() if c.updated_at else None,
        }

    @mcp.tool()
    def create_case(
        project_id: int,
        suite_id: int,
        name: str,
        scenario: str = '',
        expected: str = '',
        setup: str = '',
        teardown: str = '',
        description: str = '',
        estimate: int | None = None,
        steps: list[dict] | None = None,
        label_ids: list[int] | None = None,
    ) -> dict:
        """Create a test case. Supports two modes: simple (scenario/expected) or multi-step.

        Args:
            project_id: Project ID
            suite_id: Suite ID to place the case in
            name: Test case name
            scenario: Test scenario text (used when steps is not provided)
            expected: Expected result (used when steps is not provided)
            setup: Preconditions
            teardown: Postconditions
            description: Description
            estimate: Estimated execution time (minutes)
            steps: Array of steps for multi-step mode. Each: {"name": str, "scenario": str, "expected": str}. When provided, the case uses step-based format instead of single scenario.
            label_ids: Array of label IDs to attach to the case. Use list_labels to get available IDs.
        """
        from testy.tests_description.models import TestCase, TestCaseStep

        is_steps = bool(steps)
        with transaction.atomic():
            case = TestCase.objects.create(
                project_id=project_id,
                suite_id=suite_id,
                name=name,
                scenario='' if is_steps else scenario,
                expected='' if is_steps else expected,
                setup=setup,
                teardown=teardown,
                description=description,
                estimate=estimate,
                is_steps=is_steps,
            )
            if is_steps:
                for i, step in enumerate(steps):
                    TestCaseStep.objects.create(
                        project_id=project_id,
                        test_case=case,
                        name=step.get('name', f'Step {i + 1}'),
                        scenario=step.get('scenario', ''),
                        expected=step.get('expected', ''),
                        sort_order=i,
                    )
            if label_ids:
                _attach_labels(case, label_ids)

        return {
            'id': case.id,
            'name': case.name,
            'suite_id': case.suite_id,
            'is_steps': case.is_steps,
        }

    @mcp.tool()
    def create_cases_bulk(project_id: int, suite_id: int, cases: list[dict]) -> list[dict]:
        """Create multiple test cases in one atomic operation. Key tool for AI-driven test generation.

        Args:
            project_id: Project ID
            suite_id: Suite ID to place cases in
            cases: Array of test cases. Each: {"name": str, "scenario": str, "expected": str, "setup": str, "teardown": str, "description": str, "estimate": int, "steps": [{"name": str, "scenario": str, "expected": str}], "label_ids": [int]}. When "steps" is provided, the case uses step-based format. "label_ids" attaches labels.

        Maximum 100 cases per call.
        """
        from testy.tests_description.models import TestCase, TestCaseStep

        if len(cases) > MAX_BULK_CASES:
            raise ValueError(f'Maximum {MAX_BULK_CASES} cases per call, got {len(cases)}')

        created = []
        with transaction.atomic():
            for case_data in cases:
                steps_data = case_data.get('steps')
                is_steps = bool(steps_data)
                case = TestCase.objects.create(
                    project_id=project_id,
                    suite_id=suite_id,
                    name=case_data['name'],
                    scenario='' if is_steps else case_data.get('scenario', ''),
                    expected='' if is_steps else case_data.get('expected', ''),
                    setup=case_data.get('setup', ''),
                    teardown=case_data.get('teardown', ''),
                    description=case_data.get('description', ''),
                    estimate=case_data.get('estimate'),
                    is_steps=is_steps,
                )
                if is_steps:
                    for i, step in enumerate(steps_data):
                        TestCaseStep.objects.create(
                            project_id=project_id,
                            test_case=case,
                            name=step.get('name', f'Step {i + 1}'),
                            scenario=step.get('scenario', ''),
                            expected=step.get('expected', ''),
                            sort_order=i,
                        )
                case_label_ids = case_data.get('label_ids')
                if case_label_ids:
                    _attach_labels(case, case_label_ids)
                created.append({'id': case.id, 'name': case.name, 'is_steps': is_steps})

        return created

    @mcp.tool()
    def update_case(
        case_id: int,
        name: str | None = None,
        suite_id: int | None = None,
        scenario: str | None = None,
        expected: str | None = None,
        setup: str | None = None,
        teardown: str | None = None,
        description: str | None = None,
        estimate: int | None = None,
        steps: list[dict] | None = None,
        label_ids: list[int] | None = None,
    ) -> dict:
        """Update a test case. Can switch between simple and multi-step modes.

        Args:
            case_id: Test case ID
            name: New name
            suite_id: Move to another suite
            scenario: New test scenario (simple mode)
            expected: New expected result (simple mode)
            setup: New preconditions
            teardown: New postconditions
            description: New description
            estimate: New time estimate (minutes)
            steps: Replace steps with new ones. Each: {"name": str, "scenario": str, "expected": str}. Pass empty list [] to switch to simple mode.
            label_ids: Replace labels. Pass array of label IDs. Pass empty list [] to remove all labels.
        """
        from testy.tests_description.models import TestCase, TestCaseStep

        case = TestCase.objects.get(id=case_id, is_deleted=False)
        fields = {
            'name': name, 'suite_id': suite_id, 'scenario': scenario,
            'expected': expected, 'setup': setup, 'teardown': teardown,
            'description': description, 'estimate': estimate,
        }
        for field, value in fields.items():
            if value is not None:
                setattr(case, field, value)

        with transaction.atomic():
            if steps is not None:
                case.steps.filter(is_deleted=False).update(is_deleted=True)
                if steps:
                    case.is_steps = True
                    case.scenario = ''
                    case.expected = ''
                    for i, step in enumerate(steps):
                        TestCaseStep.objects.create(
                            project_id=case.project_id,
                            test_case=case,
                            name=step.get('name', f'Step {i + 1}'),
                            scenario=step.get('scenario', ''),
                            expected=step.get('expected', ''),
                            sort_order=i,
                        )
                else:
                    case.is_steps = False
            if label_ids is not None:
                _sync_labels(case, label_ids)
            case.save()

        return {'id': case.id, 'name': case.name, 'suite_id': case.suite_id, 'is_steps': case.is_steps}

    @mcp.tool()
    def delete_case(case_id: int) -> dict:
        """Delete a test case (soft delete).

        Args:
            case_id: Test case ID
        """
        from testy.tests_description.models import TestCase

        case = TestCase.objects.get(id=case_id, is_deleted=False)
        case.is_deleted = True
        case.save()
        return {'deleted': True, 'id': case_id}
