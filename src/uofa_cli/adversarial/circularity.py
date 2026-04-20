"""Extract-vs-generation model circularity check (§7.2)."""

from __future__ import annotations

from dataclasses import dataclass

from uofa_cli import paths

DEFAULT_EXTRACT_MODEL = "qwen3:4b"


class CircularityViolation(Exception):
    """Raised when the generation model matches the extract model in a blocking way."""


@dataclass
class CircularityResult:
    generation_model: str
    extract_model: str
    matches: bool
    exit_code: int
    warning: str | None


def resolve_extract_model() -> str:
    """Resolve the effective extract model.

    Order: project uofa.toml extract.model → DEFAULT_EXTRACT_MODEL.
    """
    try:
        project_root = paths.find_project_root()
    except Exception:
        project_root = None
    if project_root is None:
        return DEFAULT_EXTRACT_MODEL
    try:
        cfg = paths.load_project_config(project_root)
    except Exception:
        return DEFAULT_EXTRACT_MODEL
    model = cfg.get("model")
    return model if model else DEFAULT_EXTRACT_MODEL


def check_circularity(
    generation_model: str,
    extract_model: str,
    *,
    strict: bool,
    allow_circular: bool,
    explicit_override: bool,
) -> CircularityResult:
    """Apply the three-mode circularity policy from §7.2.

    Exit-code matrix:

    - No match: exit 0, no warning.
    - Match, strict mode (regardless of allow_circular): exit 4.
    - Match, explicit ``--model`` override without allow_circular: exit 4.
    - Match, allow_circular: exit 0 with prominent warning.
    - Match, spec-default (no override, no strict): exit 0 with soft warning.
    """
    matches = _models_equivalent(generation_model, extract_model)
    if not matches:
        return CircularityResult(
            generation_model=generation_model,
            extract_model=extract_model,
            matches=False,
            exit_code=0,
            warning=None,
        )

    if strict:
        return CircularityResult(
            generation_model=generation_model,
            extract_model=extract_model,
            matches=True,
            exit_code=4,
            warning=(
                f"strict-circularity: generation model {generation_model!r} matches "
                f"extract model {extract_model!r}. Refusing to run."
            ),
        )

    if explicit_override and not allow_circular:
        return CircularityResult(
            generation_model=generation_model,
            extract_model=extract_model,
            matches=True,
            exit_code=4,
            warning=(
                f"--model {generation_model!r} matches the configured extract model, "
                f"which would produce circular validation. Pass --allow-circular-model "
                f"to proceed anyway or change the generation model."
            ),
        )

    if allow_circular:
        return CircularityResult(
            generation_model=generation_model,
            extract_model=extract_model,
            matches=True,
            exit_code=0,
            warning=(
                f"--allow-circular-model: generation model {generation_model!r} matches "
                f"extract model {extract_model!r}. Results may be circular."
            ),
        )

    return CircularityResult(
        generation_model=generation_model,
        extract_model=extract_model,
        matches=True,
        exit_code=0,
        warning=(
            f"adversarial generator model {generation_model!r} matches extract model "
            f"{extract_model!r}. This may produce circular validation results. "
            f"Proceeding anyway."
        ),
    )


def _models_equivalent(a: str, b: str) -> bool:
    """Compare model identifiers tolerating the ``ollama/`` prefix."""
    return _normalize_model(a) == _normalize_model(b)


def _normalize_model(m: str) -> str:
    m = m.strip().lower()
    if m.startswith("ollama/"):
        m = m[len("ollama/") :]
    return m
