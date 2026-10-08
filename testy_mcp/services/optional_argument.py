from pydantic import Field


class OptionalArgument:
    """Distinguish omitted values from null in Python and SDK argument models."""

    UNSET = Field(default_factory=lambda: OptionalArgument.UNSET)
