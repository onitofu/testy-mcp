from jsonschema import Draft202012Validator
from rest_framework.exceptions import ValidationError


class ToolArguments:
    @staticmethod
    def validate(tool, arguments):
        schema = {**tool.parameters, "additionalProperties": False}
        errors = list(Draft202012Validator(schema).iter_errors(arguments))
        if errors:
            details = {}
            for error in errors:
                path = ".".join(str(part) for part in error.absolute_path) or "arguments"
                details.setdefault(path, []).append(error.message)
            raise ValidationError(details)
