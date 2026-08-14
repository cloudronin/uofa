#!/usr/bin/env python3
"""Capture the Credibility Inspector's four-step flow from the live Space.

Screenshots in a thesis chapter should be reproducible, so this is a script
rather than a set of hand-taken images: re-run it after any UI change and the
figures regenerate against whatever is actually deployed.

    python dev/tools/scripts/capture_inspector_screenshots.py

Costs one metered analysis at the hosted provider (~$0.006) because it drives
the real pipeline. Uses the BUNDLED SAMPLE, never uploaded evidence, so every
figure shows data that is already public and that a reader can reproduce.

A real viewport is set explicitly. Headless Chrome defaults can report an
innerHeight of 0, which makes Gradio's vh-based layout compute a 21,000px page
and a 412px single-row textbox -- an artifact that looks exactly like a layout
bug until you check innerHeight.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

SPACE = "https://cloudronin-uofa-demo.hf.space/"
OUT = Path(__file__).resolve().parents[3] / "docs" / "img" / "inspector"
VIEWPORT = {"width": 1280, "height": 900}

# (filename, what we wait for, what the figure shows)
STEPS = [
    ("01-start.png", "Step 1: start, with the pre-upload disclosure"),
    ("02-confirm-standard.png", "Step 2: the router's choice, open to correction"),
    ("03-confirm-status.png", "Step 3: where human judgment enters"),
    ("04-reviewer.png", "Step 4: the Reviewer reading"),
    ("05-author.png", "Step 4: the same analysis, Author reading"),
]


def _shot(page, name: str, note: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    page.screenshot(path=str(path), full_page=True)
    kb = path.stat().st_size // 1024
    print(f"  {name:28s} {kb:4d} KB   {note}")


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=180, help="seconds to wait for the analysis")
    args = ap.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, color_scheme="dark",
                                device_scale_factor=1)
        # NOT networkidle: Gradio holds a live connection open, so the network
        # is never idle and the wait times out on a page that loaded fine.
        page.goto(SPACE, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_selector("text=Step 1 of 4", timeout=120_000)
        _shot(page, *STEPS[0])

        # Step 1 -> 2. The sample, deliberately: public data, reproducible.
        page.get_by_role("button", name="Try a sample evidence set").click()
        page.wait_for_selector("text=Step 2 of 4", timeout=120_000)
        _shot(page, *STEPS[1])

        # Step 2 -> 3. This is the metered call.
        page.get_by_role("button", name="Analyze evidence").first.click()
        page.wait_for_selector("text=Step 3 of 4", timeout=args.timeout * 1000)
        _shot(page, *STEPS[2])

        # Step 3 -> 4. No status is changed: the figure should show the flow,
        # not a staged correction.
        page.get_by_role("button", name="See my gaps").first.click()
        page.wait_for_selector("text=At a glance", timeout=args.timeout * 1000)
        time.sleep(1)
        _shot(page, *STEPS[3])

        page.get_by_role("radio", name="Author (Gap-Finder)").click()
        time.sleep(1)
        _shot(page, *STEPS[4])

        browser.close()

    print(f"\nWrote {len(STEPS)} figures to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
