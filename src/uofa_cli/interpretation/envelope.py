"""Interpretation envelope JSON schema (spec v0.4 §4.5).

The envelope wraps a command's structured output with the interpretation
payload. Same shape across all four commands; per-command differences live
in the `interpretation.<function-result-fields>` slots.

```
{
  "command": "rules",
  "command_version": "0.6.0",
  "structured_output": {...},
  "interpretation": {
    "interpretation_timestamp": "2026-12-15T22:30:00Z",
    "interpretation_model": "qwen3.5:4b",
    "interpretation_backend": "ollama",
    "interpretation_version": "0.2.0",
    "functions_run": ["explain", "group", "contextualize", "cross"],
    "explanations": [...],
    "groupings": {...},
    "contextual_severity": {...},
    "cross_patterns": [...],
    "narratives": [...]   // present only when check has C4 output
  }
}
```

Caching keys (spec §4.7) are computed from the structured_output hash plus
the model + backend + interpretation_version + prompt template version, so
the envelope's metadata fields must be stable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

# Stable identifier for the envelope schema itself. Bump on
# breaking-format changes per spec §5 (semver: major.minor.patch).
#
# 0.4.0 — P-B Round 1 follow-up: dropped the `confidence` field from
#         explanations. Two iterations on bundled qwen3.5:4b produced
#         11/11 "high" regardless of explicit criteria — the model
#         can't self-assess on this task, so the field was misleading
#         (always-true signal is no signal). Now: three prose fields
#         (affected_evidence_summary, gap_description, relevance_to_cou).
# 0.3.0 — P-B Round 1: explanation field set changed from single
#         `explanation` to four fields. Cache entries produced under
#         0.2.0 are invalidated automatically.
# 0.2.0 — initial P-B (Round 0)
INTERPRETATION_VERSION = "0.4.0"


Command = Literal["rules", "check", "diff", "shacl"]


@dataclass(frozen=True)
class Interpretation:
    """The interpretation payload (everything under the `interpretation` key).

    Per-function results live in the optional fields. A function that didn't
    run for a given command leaves its field empty/None — consumers (Tauri,
    text formatter) branch on `function in functions_run` rather than
    presence to handle the "ran but found nothing" case correctly.
    """

    interpretation_timestamp: str
    interpretation_model: str
    interpretation_backend: str
    interpretation_version: str
    functions_run: list[str]

    # Per-function result slots (spec §4.5). Empty when not applicable.
    explanations: list[dict] = field(default_factory=list)
    groupings: dict = field(default_factory=dict)
    contextual_severity: dict = field(default_factory=dict)
    cross_patterns: list[dict] = field(default_factory=list)
    narratives: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class InterpretationEnvelope:
    """Top-level envelope wrapping structured_output + interpretation.

    Identical shape across commands (spec §4.5). The `command_version`
    captures the CLI version that produced the structured_output —
    interpretation results from a CLI v0.6.x are not assumed compatible
    with v0.7.x structured output (re-run rather than re-interpret).
    """

    command: Command
    command_version: str
    structured_output: dict | list
    interpretation: Interpretation | None = None  # None on graceful degradation

    def to_dict(self) -> dict:
        """JSON-serializable dict; matches spec §4.5 examples exactly."""
        out: dict = {
            "command": self.command,
            "command_version": self.command_version,
            "structured_output": self.structured_output,
        }
        out["interpretation"] = (
            asdict(self.interpretation) if self.interpretation is not None else None
        )
        return out


def make_envelope(
    *,
    command: Command,
    command_version: str,
    structured_output: dict | list,
    backend_name: str,
    model_name: str,
    functions_run: list[str],
    explanations: list[dict] | None = None,
    groupings: dict | None = None,
    contextual_severity: dict | None = None,
    cross_patterns: list[dict] | None = None,
    narratives: list[dict] | None = None,
    timestamp: str | None = None,
) -> InterpretationEnvelope:
    """Construct an InterpretationEnvelope with current timestamp.

    Defaults to UTC now in ISO-8601; tests can pin via `timestamp=`.
    """
    interpretation = Interpretation(
        interpretation_timestamp=timestamp or _now_iso8601_utc(),
        interpretation_model=model_name,
        interpretation_backend=backend_name,
        interpretation_version=INTERPRETATION_VERSION,
        functions_run=list(functions_run),
        explanations=list(explanations or []),
        groupings=dict(groupings or {}),
        contextual_severity=dict(contextual_severity or {}),
        cross_patterns=list(cross_patterns or []),
        narratives=list(narratives or []),
    )
    return InterpretationEnvelope(
        command=command,
        command_version=command_version,
        structured_output=structured_output,
        interpretation=interpretation,
    )


def _now_iso8601_utc() -> str:
    """ISO-8601 timestamp with Z suffix, matching spec §4.5 examples."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
