"""Put the repo root on sys.path so `import harness` resolves to the top-level
harness/ package (it is experiment tooling, not part of the installed wheel).

Needed under bare `pytest` (where cwd isn't auto-added); harmless under
`python -m pytest`.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
