"""Calculation-verification rules switch (`--calcverif`).

The W-CV rules ship inside a pack as a default-off block (`calcverif` in the
detection payload, `"enabled": false`). They are ordinary forward weakener
rules: when switched on, their rule file is appended to the normal C3 rules
list for that one invocation. Nothing else turns them on.

Modules:
  config — pack-config + CLI flag resolver (mirrors uofa_cli.oos.config)
"""
