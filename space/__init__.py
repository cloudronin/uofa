"""UofA Gap-Finder Space - a thin Gradio lead-magnet over the uofa pipeline.

This package is intentionally OUTSIDE src/uofa_cli so its Gradio dependency
never leaks into the `uofa` wheel; it imports `uofa_cli.*` in-process.
"""
