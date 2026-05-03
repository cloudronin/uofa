"""UofA CLI — create, validate, and sign Unit of Assurance evidence packages."""

from __future__ import annotations

# Read the version from the installed wheel's metadata so `uofa --version`
# stays in sync with pyproject.toml automatically. Pre-v0.7.0 this was a
# hardcoded literal that drifted (every v0.5.x..v0.6.x release reported
# "0.5.0" because nobody remembered to bump it here too). Falls back to
# "unknown" only when the package is being run from a checkout that hasn't
# been pip-installed (rare; CI and end users always go through pip).
try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    try:
        __version__ = _pkg_version("uofa")
    except PackageNotFoundError:
        __version__ = "unknown"
except ImportError:  # pragma: no cover — Python <3.8, not supported
    __version__ = "unknown"
