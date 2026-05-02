"""Per-function interpretation implementations (spec v0.4 §2.1-§2.5).

Importing this package registers every function with the dispatcher (each
submodule is decorated with `@applies_to_commands(...)` at module-load
time). The interpretation pipeline imports this package once at startup so
registration is a side-effect of normal import.

Phases:
- P-B (this module): explain — plain-language firing explanation
- P-F: group — clustering
- P-G: contextualize — severity contextualization
- P-H: cross — cross-item pattern recognition
- P-I: narrative — surviving-set narrative
- P-J: explain extension for diff
- P-K: explain/group/contextualize for shacl
"""

from __future__ import annotations

# Side-effect imports — each module's decorator registers with the dispatcher.
from uofa_cli.interpretation.functions import explain  # noqa: F401
from uofa_cli.interpretation.functions import group  # noqa: F401
from uofa_cli.interpretation.functions import contextualize  # noqa: F401
from uofa_cli.interpretation.functions import cross  # noqa: F401
from uofa_cli.interpretation.functions import narrative  # noqa: F401

__all__ = ["explain", "group", "contextualize", "cross", "narrative"]
