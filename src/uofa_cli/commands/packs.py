"""uofa packs — list and inspect installed domain packs."""

from uofa_cli.output import header, info, result_line
from uofa_cli import paths

HELP = "list and inspect installed domain packs"


def add_arguments(parser):
    parser.add_argument("name", nargs="?", help="pack name to inspect (default: list all)")
    parser.add_argument("--detail", action="store_true", dest="pack_verbose",
                        help="show detailed pack information")


def run(args) -> int:
    if args.name:
        return _show_pack(args.name, args.pack_verbose)
    return _list_packs()


def _list_packs() -> int:
    pack_names = paths.list_packs()
    if not pack_names:
        info("No packs installed.")
        return 0

    active = paths.get_active_pack()
    header("Installed packs")

    for name in pack_names:
        try:
            manifest = paths.pack_manifest(name)
        except FileNotFoundError:
            continue

        version = manifest.get("version", "?")
        desc = manifest.get("description", "")
        # Truncate description for list view
        short_desc = desc[:60] + "..." if len(desc) > 60 else desc

        markers = []
        if name == "core":
            markers.append("always loaded")
        if name in active:
            markers.append("active")
        marker = f"  [{', '.join(markers)}]" if markers else ""

        factors = manifest.get("factors", "?")
        if factors is None:
            factors = "any"
        patterns = manifest.get("weakener_patterns", "?")
        info(f"  {name:<12} v{version:<8} {short_desc} ({factors} factors, {patterns} patterns){marker}")

    return 0


def _show_pack(name: str, verbose: bool) -> int:
    try:
        manifest = paths.pack_manifest(name)
    except FileNotFoundError:
        from uofa_cli.output import error
        error(f"Pack not found: {name}")
        available = paths.list_packs()
        if available:
            info(f"  Available packs: {', '.join(available)}")
        return 1

    pdir = paths.pack_dir(name)

    header(f"Pack: {name} (v{manifest.get('version', '?')})")
    info(f"  Description: {manifest.get('description', '—')}")

    standards = manifest.get("standards", [])
    if standards:
        info(f"  Standards:   {', '.join(standards)}")

    shapes_rel = manifest.get("shapes", "")
    if shapes_rel:
        shapes_path = pdir / shapes_rel
        info(f"  Shapes:      {shapes_path.relative_to(paths.find_repo_root())}")

    rules_rel = manifest.get("rules")
    patterns = manifest.get("weakener_patterns", "?")
    if rules_rel:
        rules_path = pdir / rules_rel
        info(f"  Rules:       {rules_path.relative_to(paths.find_repo_root())} ({patterns} patterns)")
    else:
        info(f"  Rules:       none ({patterns} patterns)")

    template = manifest.get("template", "")
    if template:
        info(f"  Template:    {pdir.relative_to(paths.find_repo_root()) / template}")

    prompt = manifest.get("prompt", "")
    if prompt:
        info(f"  Prompt:      {pdir.relative_to(paths.find_repo_root()) / prompt}")

    factors = manifest.get("factors")
    info(f"  Factors:     {factors if factors is not None else 'any (standards-agnostic)'}")
    info(f"  Author:      {manifest.get('author', '—')}")
    info(f"  License:     {manifest.get('license', '—')}")

    return 0
