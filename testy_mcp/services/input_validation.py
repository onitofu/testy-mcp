from decimal import Decimal, localcontext

from pytimeparse.timeparse import COMPILED_SIGN, COMPILED_TIMEFORMATS, MULTIPLIERS
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class InputValidation:
    @staticmethod
    def fields(model, data):
        builder = serializers.ModelSerializer()
        validated = {}
        for name, value in data.items():
            field = model._meta.get_field(name)
            if value is not None:
                if field.get_internal_type() in {"CharField", "TextField"}:
                    if not isinstance(value, str):
                        raise ValidationError({name: "Must be a string."})
                elif field.get_internal_type() in {"IntegerField", "PositiveIntegerField"}:
                    if type(value) is not int:
                        raise ValidationError({name: "Must be an integer."})
            field_type, kwargs = builder.build_standard_field(name, field)
            try:
                validated[name] = field_type(**kwargs).run_validation(value)
            except ValidationError as exc:
                raise ValidationError({name: exc.detail}) from exc
        return validated

    @staticmethod
    def estimate(value):
        from testy.serializer_fields import EstimateField
        from testy.tests_description.models import TestCase
        from testy.tests_description.validators import EstimateValidator

        if value is None:
            return None
        if type(value) not in {int, str}:
            raise ValidationError({"estimate": "Must be integer minutes or a duration string."})
        duration = EstimateField().run_validation(value)
        EstimateValidator()({"estimate": duration})
        InputValidation._validate_estimate_precision(duration)
        seconds = EstimateField(to_workday=False).run_validation(duration)
        if int(seconds) != seconds:
            raise ValidationError({"estimate": "Must represent a whole number of seconds."})
        return int(TestCase._meta.get_field("estimate").to_python(duration))

    @staticmethod
    def _validate_estimate_precision(duration):
        if duration.isnumeric():
            duration = f"{duration}m"
        unsigned = COMPILED_SIGN.match(duration).group("unsigned")
        for pattern in COMPILED_TIMEFORMATS:
            match = pattern.match(unsigned)
            if match and match.group(0).strip():
                with localcontext() as context:
                    context.prec = max(28, len(duration) + 16)
                    seconds = sum(
                        Decimal(value) * MULTIPLIERS[unit]
                        for unit, value in match.groupdict().items()
                        if value is not None
                    )
                    if seconds != seconds.to_integral_value():
                        raise ValidationError(
                            {"estimate": "Must represent a whole number of seconds."}
                        )
                return

    @staticmethod
    def format_estimate(seconds):
        from testy.serializer_fields import EstimateField

        return EstimateField().to_representation(seconds)

    @classmethod
    def case(cls, data):
        from testy.tests_description.models import TestCase, TestCaseStep

        if not isinstance(data, dict) or "name" not in data:
            raise ValidationError("Each case must have a name.")
        allowed = {
            "name",
            "scenario",
            "expected",
            "setup",
            "teardown",
            "description",
            "estimate",
            "steps",
            "label_ids",
        }
        if data.keys() - allowed:
            raise ValidationError("Unknown case fields.")
        fields = {
            key: value
            for key, value in data.items()
            if key not in {"steps", "label_ids", "estimate"}
        }
        validated = cls.fields(TestCase, fields)
        if "estimate" in data:
            validated["estimate"] = cls.estimate(data["estimate"])
        if "label_ids" in data:
            labels = data["label_ids"]
            if labels is not None and (
                not isinstance(labels, list) or any(type(label) is not int for label in labels)
            ):
                raise ValidationError({"label_ids": "Must be an array of integer IDs."})
            validated["label_ids"] = labels
        if "steps" in data:
            steps = data["steps"]
            if steps is not None and not isinstance(steps, list):
                raise ValidationError({"steps": "Must be an array."})
            validated["steps"] = None if steps is None else []
            for index, step in enumerate(steps or []):
                if not isinstance(step, dict) or step.keys() - {"name", "scenario", "expected"}:
                    raise ValidationError({"steps": "Invalid step fields."})
                payload = {"name": f"Step {index + 1}", "scenario": "", "expected": "", **step}
                validated["steps"].append(cls.fields(TestCaseStep, payload))
        return validated

    @classmethod
    def suites(cls, suites):
        from testy.tests_description.models import TestSuite

        if not isinstance(suites, list):
            raise ValidationError("Suites must be a list.")
        validated = []
        for suite in suites:
            if not isinstance(suite, dict) or "name" not in suite:
                raise ValidationError("Each suite must have a name.")
            if suite.keys() - {"name", "description", "children"}:
                raise ValidationError("Unknown suite fields.")
            fields = {key: value for key, value in suite.items() if key != "children"}
            validated.append(
                {**cls.fields(TestSuite, fields), "children": cls.suites(suite.get("children", []))}
            )
        return validated

    @classmethod
    def plan(cls, data):
        from testy.tests_representation.models import TestPlan
        from testy.tests_representation.validators import DateRangeValidator

        validated = cls.fields(TestPlan, data)
        DateRangeValidator()(validated)
        return validated

    @classmethod
    def result(cls, data):
        from testy.tests_representation.models import TestResult

        return cls.fields(TestResult, data)

    @classmethod
    def result_item(cls, data):
        allowed = {"test_id", "case_name", "status", "comment", "execution_time"}
        if not isinstance(data, dict) or data.keys() - allowed:
            raise ValidationError("Invalid result fields.")
        if not isinstance(data.get("status"), str) or not data["status"].strip():
            raise ValidationError({"status": "A status name is required."})
        if "test_id" in data:
            if type(data["test_id"]) is not int:
                raise ValidationError({"test_id": "Must be an integer ID."})
        elif not isinstance(data.get("case_name"), str) or not data["case_name"].strip():
            raise ValidationError("Each result must have a test_id or case_name.")
        fields = {"comment": data.get("comment", ""), "execution_time": data.get("execution_time")}
        return {**data, **cls.result(fields)}
