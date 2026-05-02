"""Jinja2 prompt-template loader (spec v0.4 §4.4 / §6.1 / §6.2).

Templates live in two places, looked up in this order:

1. Pack-specific:
   `<repo>/packs/<pack>/prompts/<command>/<function>.jinja2`
2. Bundled defaults:
   `<repo>/src/uofa_cli/interpretation/templates/<command>/<function>.jinja2`

The bundled defaults make `--explain` work on every pack out of the box;
pack-specific templates let pack authors customize wording (NASA-STD-7009B
uses NASA terminology, V&V 40 uses FDA terminology).

Jinja2 is imported lazily so the module loads without it (graceful for
test environments without `[explain]` extras installed). When templates
are actually rendered, BackendNotInstalled is raised with a clear hint.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from uofa_cli import paths
from uofa_cli.llm.errors import BackendNotInstalled


# Where bundled-default templates live in the source tree. Resolved relative
# to this module so it works after `pip install` (templates ship in the wheel
# under `src/uofa_cli/interpretation/templates/`).
_BUNDLED_TEMPLATES_DIR = Path(__file__).parent / "templates"


def template_path(command: str, function: str, pack_name: str | None = None) -> Path | None:
    """Return the path of the highest-priority template for (command, function).

    Resolution order:
        1. `packs/<pack_name>/prompts/<command>/<function>.jinja2`  (if pack_name)
        2. `<bundled_templates_dir>/<command>/<function>.jinja2`
        3. None — caller decides what to do (skip the function, error, etc.)

    The two-tier fallback means new packs work without authoring any
    templates: the bundled defaults handle all four target commands.
    """
    if pack_name:
        try:
            pack_dir = paths.pack_dir(pack_name)
            candidate = pack_dir / "prompts" / command / f"{function}.jinja2"
            if candidate.is_file():
                return candidate
        except (FileNotFoundError, KeyError):
            pass

    bundled = _BUNDLED_TEMPLATES_DIR / command / f"{function}.jinja2"
    if bundled.is_file():
        return bundled

    return None


def load_template(command: str, function: str, pack_name: str | None = None):
    """Load a Jinja2 Template object for (command, function, pack_name).

    Returns the template; raises FileNotFoundError if neither pack-specific
    nor bundled template exists, and BackendNotInstalled if Jinja2 isn't
    available in the environment.
    """
    path = template_path(command, function, pack_name)
    if path is None:
        raise FileNotFoundError(
            f"No template found for command={command!r}, function={function!r}, "
            f"pack={pack_name!r}. Looked in pack `prompts/{command}/{function}.jinja2` "
            f"and bundled defaults at {_BUNDLED_TEMPLATES_DIR}/{command}/{function}.jinja2."
        )
    return _compile_template(path)


def render(command: str, function: str, pack_name: str | None, **vars) -> str:
    """Render the template for (command, function, pack_name) with **vars."""
    template = load_template(command, function, pack_name)
    return template.render(**vars)


@lru_cache(maxsize=128)
def _compile_template(path: Path):
    """Compile a Jinja2 template from disk. Cached by path."""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: PLC0415
    except ImportError as exc:
        raise BackendNotInstalled(
            "Jinja2 is not installed",
            suggestion="pip install uofa[extract] (or pip install jinja2)",
        ) from exc

    env = Environment(
        loader=FileSystemLoader(str(path.parent)),
        autoescape=select_autoescape(disabled_extensions=("jinja2",)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=False,
    )
    return env.get_template(path.name)


def has_template(command: str, function: str, pack_name: str | None = None) -> bool:
    """True if either a pack template OR a bundled default exists.

    Lets the dispatcher skip a function silently when no template exists for
    a given (command, function) pair — useful while the bundled-template set
    is being built out incrementally over Phases 5-12.
    """
    return template_path(command, function, pack_name) is not None
