"""CLI for the AirfRANS corpus harness: `python -m harness <subcommand>`.

Subcommands chain the experiment: pull → select → train → corpus → gap. `pull`,
`select`, `train`, and `corpus` need the real AirfRANS data (gated on the
`airfrans` package + a local cache); `gap` is pure arithmetic over the committed
per-case table. No LLM, no verdict — the harness measures.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _add_common(p, *, task=True, root=True, out=True):
    if task:
        p.add_argument("--task", default="aoa", choices=["aoa", "reynolds"])
    if root:
        p.add_argument("--root", type=Path, default=None, help="AirfRANS cache dir (UOFA_AIRFRANS_DIR)")
    if out:
        p.add_argument("--out", type=Path, default=Path("dev/build/airfrans-exp"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="harness", description="AirfRANS corpus harness (Experiment A)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pull = sub.add_parser("pull", help="fetch + cache AirfRANS for a task")
    _add_common(p_pull, out=False)
    p_sel = sub.add_parser("select", help="Step 0: choose the extrapolation split (error-vs-parameter)")
    _add_common(p_sel, task=False)
    p_tr = sub.add_parser("train", help="train the honest surrogate on the in-envelope split")
    _add_common(p_tr)
    p_co = sub.add_parser("corpus", help="run SIP + check over the split → per-case table")
    _add_common(p_co)
    p_co.add_argument("--limit", type=int, default=None)
    p_gap = sub.add_parser("gap", help="compute the error-gap number from the per-case table")
    p_gap.add_argument("--table", type=Path, default=Path("dev/build/airfrans-exp/per_case.jsonl"))
    p_slice = sub.add_parser("slice", help="slice fired cases by envelope side + geometry (thickness)")
    p_slice.add_argument("--table", type=Path, default=Path("dev/build/airfrans-exp/per_case.jsonl"))
    p_slice.add_argument("--param", default="aoa", choices=["aoa", "reynolds"])

    args = parser.parse_args(argv)
    return _dispatch(args)


def _dispatch(args) -> int:
    if args.cmd == "pull":
        from harness.airfrans_pull import load_airfrans
        corpus = load_airfrans(args.task, args.root)
        print(f"pulled airfrans task={args.task}: {len(corpus.train)} train, "
              f"{len(corpus.evaluation)} eval; envelope={corpus.envelope}")
        return 0

    if args.cmd == "select":
        from harness import select_split
        from harness.airfrans_pull import TASKS, load_airfrans
        results = {t: select_split.evaluate_task(load_airfrans(t, args.root)) for t in TASKS}
        select_split.write_error_vs_parameter(results, args.out)
        chosen, _ = select_split.choose(results)
        (args.out / "chosen_split.txt").write_text(chosen + "\n", encoding="utf-8")
        print(select_split.render(results))
        print(f"\n[chosen split written to {args.out / 'chosen_split.txt'}]")
        return 0

    if args.cmd == "train":
        from harness import train_surrogate
        from harness.airfrans_pull import load_airfrans
        corpus = load_airfrans(args.task, args.root)
        info = train_surrogate.train_and_save(corpus, args.out)
        print(f"trained on task={args.task}; envelope={info['envelope']}; model={info['model_path']}")
        return 0

    if args.cmd == "corpus":
        from harness import run_corpus
        from harness.airfrans_pull import load_airfrans
        corpus = load_airfrans(args.task, args.root)
        bounds = json.loads((args.out / "declared_envelope.json").read_text())
        envelope = {k: tuple(v) for k, v in bounds["envelope"].items()}
        rows = run_corpus.run_corpus(corpus, args.out / "surrogate.joblib", envelope, args.out, limit=args.limit)
        fired = sum(1 for r in rows if r["w_surr_03_fired"])
        print(f"corpus: {len(rows)} cases ({fired} fired W-SURR-03, {len(rows)-fired} not) "
              f"→ {args.out / 'per_case.jsonl'}")
        return 0

    if args.cmd == "gap":
        from harness import error_gap
        rows = error_gap.load_table(args.table)
        split_file = args.table.parent / "chosen_split.txt"
        label = (split_file.read_text().strip() + " extrapolation"
                 if split_file.exists() else "extrapolation")
        print(error_gap.render_report(rows, split_label=label))
        return 0

    if args.cmd == "slice":
        from harness import asymmetry_slice, error_gap
        rows = error_gap.load_table(args.table)
        env_file = args.table.parent / "declared_envelope.json"
        bounds = json.loads(env_file.read_text())["envelope"]
        envelope = {k: tuple(v) for k, v in bounds.items()}
        print(asymmetry_slice.render(rows, envelope, param=args.param))
        return 0

    return 2
