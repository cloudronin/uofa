"""uofa adversarial — synthetic credibility evidence generation for coverage experiments."""

from uofa_cli.adversarial.spec_loader import (
    AdversarialSpec,
    SpecValidationError,
    load_spec,
)

__all__ = [
    "AdversarialSpec",
    "SpecValidationError",
    "load_spec",
]
