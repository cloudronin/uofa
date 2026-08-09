#!/usr/bin/env python3
"""Every package in the repo, validated, so a schema change can be proven safe.

Run before a shape change and after it, then diff. A schema edit that says "this
is additive" or "this only moves a constraint" is a claim about 62 packages, and
the only way to hold it is to validate all of them twice.

    python dev/tools/scripts/profile_baseline.py --out before.json
    ... edit shapes ...
    python dev/tools/scripts/profile_baseline.py --out after.json --diff before.json

Reports per package: the profile it declares, whether it conforms, and the paths
that failed. A package moving from conforming to non-conforming is a regression.
A package moving the other way is a change that must be intended and explained --
silently making validation easier is how a shape stops meaning anything.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "src"))

SKIP = ("/context/", "/schemas/")


def packages() -> list[pathlib.Path]:
    out = []
    for base in ("packs", "tests", "examples"):
        d = _ROOT / base
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.jsonld")):
            rel = str(p.relative_to(_ROOT))
            if any(s in f"/{rel}" for s in SKIP):
                continue
            out.append(p)
    return out


def pack_for(rel: str) -> str:
    """Which pack this package is validated under.

    Shapes are NOT all loaded at once: `all_shacl_schemas` returns core plus the
    ACTIVE packs, defaulting to `vv40`. Loading all seven shape files -- which the
    first version of this harness did -- validates every package against every
    standard's constraints, which no real invocation does and which would have
    made this instrument disagree with the tool it exists to protect.
    """
    parts = rel.split("/")
    if parts[0] == "packs" and len(parts) > 1 and parts[1] != "core":
        return parts[1]
    return "vv40"          # the open-core baseline, same default as the CLI


def shape_files(pack: str) -> list[pathlib.Path]:
    """Core + one pack, exactly as `paths.all_shacl_schemas` assembles it."""
    out = [_ROOT / "packs" / "core" / "shapes" / "uofa_shacl.ttl"]
    out += sorted((_ROOT / "packs" / pack / "shapes").glob("*.ttl"))
    return [p for p in out if p.exists()]


def has_target(path: pathlib.Path) -> bool:
    """Whether the shape has anything to validate here.

    A SHACL shape targeting `uofa:UnitOfAssurance` conforms VACUOUSLY on a file
    containing no such node -- it finds nothing to check and reports success.
    Three of the shipped nasa-7009b "examples" are exactly that: weakener
    annotation overlays that reference a package IRI living elsewhere, and
    `uofa shacl` calls them conforming.

    Without this column, "59 of 64 conforming" cannot be read: a pass on a file
    with nothing in it and a pass on a fully-populated package look identical.
    That is `control_constant_list` scoring 1.000 in a new place -- a measure
    rewarding emptiness.

    Detection checks BOTH `@type` and `type`. The packages that matter are
    compacted JSON-LD aliasing `type` to `@type` via their `@context`, and a
    first version of this check looked only at `@type` and reported that ZERO of
    64 packages had a target -- while five of them were failing validation,
    which requires a target to fail on. An implausible number is the signal;
    5 failures against 0 targets cannot both be true.
    """
    import json
    try:
        blob = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    for node in (blob.get("@graph") or [blob]):
        if not isinstance(node, dict):
            continue
        t = node.get("@type") or node.get("type") or ""
        if "UnitOfAssurance" in str(t):
            return True
    return False


def check_one(path: pathlib.Path, shapes: list[pathlib.Path]) -> dict:
    from uofa_cli.shacl_friendly import run_shacl_multi
    try:
        ok, results = run_shacl_multi(path, shapes)
    except Exception as exc:                       # unreadable / not a package
        return {"conforms": None, "error": f"{type(exc).__name__}: {exc}"[:120]}
    paths = sorted({str(r.get("path") or "") for r in results if r.get("path")})
    try:
        blob = json.loads(path.read_text())
        prof = json.dumps(blob).split("conformsToProfile")[1][:90] \
            if "conformsToProfile" in json.dumps(blob) else ""
        prof = prof.split("Profile")[1].split('"')[0] if "Profile" in prof else ""
    except Exception:
        prof = ""
    return {"conforms": bool(ok), "profile": prof, "failed_paths": paths}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--diff", type=pathlib.Path, default=None)
    args = ap.parse_args()

    pkgs = packages()
    print(f"\n  {len(pkgs)} packages, each under core + its own pack\n")
    now = {}
    for p in pkgs:
        rel = str(p.relative_to(_ROOT))
        pack = pack_for(rel)
        now[rel] = check_one(p, shape_files(pack))
        now[rel]["pack"] = pack
        now[rel]["has_target"] = has_target(p)
    args.out.write_text(json.dumps(now, indent=2, sort_keys=True) + "\n")

    conf = sum(1 for v in now.values() if v.get("conforms") is True)
    nonc = sum(1 for v in now.values() if v.get("conforms") is False)
    err = sum(1 for v in now.values() if v.get("conforms") is None)
    vac = sum(1 for v in now.values()
              if v.get("conforms") is True and not v.get("has_target"))
    print(f"  conforming {conf}   non-conforming {nonc}   unreadable {err}")
    print(f"  ...of the conforming, {vac} have NO UnitOfAssurance node and pass")
    print(f"     vacuously — the shape found nothing to check. {conf - vac} are")
    print(f"     packages that actually met their profile.")
    print(f"  wrote {args.out}")

    if args.diff:
        before = json.loads(args.diff.read_text())
        regressed, improved, changed = [], [], []
        for rel, after in sorted(now.items()):
            b = before.get(rel)
            if b is None:
                changed.append(f"NEW      {rel}")
                continue
            if b.get("conforms") and not after.get("conforms"):
                regressed.append(f"REGRESS  {rel}  now fails on "
                                 f"{after.get('failed_paths')}")
            elif not b.get("conforms") and after.get("conforms"):
                improved.append(f"NOW OK   {rel}  was failing on "
                                f"{b.get('failed_paths')}")
        for rel in sorted(set(before) - set(now)):
            changed.append(f"GONE     {rel}")

        print(f"\n  ── against {args.diff.name} ──")
        for line in regressed + improved + changed:
            print(f"    {line}")
        if not (regressed or improved or changed):
            print("    no package changed verdict")
        print(f"\n  regressions {len(regressed)}   newly conforming "
              f"{len(improved)}   appeared/disappeared {len(changed)}")
        return 1 if regressed else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
