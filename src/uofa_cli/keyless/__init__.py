"""Keyless extraction: routes that read a document without a language model.

Every route here was measured against a null model that reads nothing, and only
routes that beat their null are present. A property with no such route emits
nothing -- `minCount >= 1` in the SHACL profile is satisfied by PRESENCE, not by
correctness, so an extractor that fills every field produces a package that
validates while being mostly wrong. This project has already paid for that: 14
turbomachinery models labelled "Class II" validated while packages honestly
naming their device failed.
"""
from uofa_cli.keyless.trained import Unavailable, available, load  # noqa: F401
