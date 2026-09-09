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
    ("06-package.png", "Step 4: the signed package, offered as a download"),
]


def _shot(page, name: str, note: str, *, full_page: bool = True) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    page.screenshot(path=str(path), full_page=full_page)
    kb = path.stat().st_size // 1024
    print(f"  {name:28s} {kb:4d} KB   {note}")


def _capture_package(page, args) -> str | None:
    """Write the package figure. Returns None, or why it could not be written.

    A regression check as much as a figure. The control's absence is silent: in
    September 2026 the deployed Space rendered a SIGNED readout, told the reader
    to download the package below, and offered nothing, with no error in the UI
    and no line in the container log (see
    studies/inspector-live-verification-2026-09/).

    A bare timeout here cannot tell "the Space served no package" from "this
    script's selector is stale", and guessing between those from a checkout is
    what cost an evening the first time. So the message says which, and leaves a
    full-page screenshot to look at. Checked against gradio 6.24, the version
    space/requirements.txt pins: DownloadButton renders as <button> and this
    locator matches it.
    """
    pack = page.get_by_role("button", name="Download UofA package")
    try:
        pack.wait_for(state="visible", timeout=60_000)
    except Exception:
        hits = page.get_by_text("Download UofA package").count()
        signed = "Signed" in (page.locator("body").inner_text() or "")
        debug = OUT / "06-package-FAILED.png"
        page.screenshot(path=str(debug), full_page=True)
        return (
            "\nThe package control did not appear, so 06-package.png was not "
            "written.\n"
            f"  control text found in the page: {hits}\n"
            f"  readout claims a signature:     {signed}\n\n"
            "  0 found + signed=True is THE regression: a signed readout with\n"
            "    no package. See studies/inspector-live-verification-2026-09/.\n"
            "  0 found + signed=False means the run was never signed; check the\n"
            "    Space's UOFA_ISSUER_SIGNING_KEY secret.\n"
            "  1 or more found means the control is present and this selector\n"
            "    missed it. Fix the script, not the Space.\n\n"
            f"  Full-page screenshot written to {debug}\n"
            "  Every other figure was written and is usable.\n")

    pack.scroll_into_view_if_needed()
    time.sleep(0.5)
    # Viewport, not full page: the reader should see the control in place among
    # the reviewer's closing lines, at the size a user meets it.
    _shot(page, *STEPS[5], full_page=False)
    return None


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=180, help="seconds to wait for the analysis")
    ap.add_argument("--url", default=SPACE,
                    help="target to drive (default: the deployed Space). Point "
                         "this at a local `python -m space.app` to check that "
                         "this script still works after a UI change WITHOUT "
                         "spending a metered run to find out. Figures captured "
                         "from anywhere but the deployed Space are for checking "
                         "the script, never for the manuscript.")
    args = ap.parse_args()

    if args.url != SPACE:
        print(f"[check-run] driving {args.url}, NOT the deployed Space.")
        print("[check-run] figures written here are throwaway: do not commit them.")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, color_scheme="dark",
                                device_scale_factor=1)
        # NOT networkidle: Gradio holds a live connection open, so the network
        # is never idle and the wait times out on a page that loaded fine.
        page.goto(args.url, wait_until="domcontentloaded", timeout=120_000)
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

        # 06 is captured HERE, while the Reviewer view is still on screen.
        #
        # The package control lives inside the reviewer panel, so an earlier
        # version of this script switched to Author for 05 and then toggled back
        # for 06. That round trip is a step that can fail on a slower target for
        # reasons that have nothing to do with the control, and when it did fail
        # it was indistinguishable from the defect this check exists to catch.
        # Not leaving the panel removes the question.
        #
        # Its own figure because a full-page shot of a ~3,000px readout does not
        # show it, and the download is the whole point: the user leaves with an
        # artifact a third party can verify without trusting this site. A
        # chapter that claims that and shows no control is asserting it.
        pack_failure = _capture_package(page, args)

        page.get_by_role("radio", name="Author (Gap-Finder)", exact=True).click()
        time.sleep(1)
        _shot(page, *STEPS[4])

        browser.close()

    # Everything capturable has now been captured. Only then does a missing
    # package control end the run: an earlier version raised at that point and
    # cost the caller the figures it had already been able to take, which is a
    # bad trade for a check that is meant to inform rather than obstruct.
    if pack_failure:
        print(pack_failure, file=sys.stderr)
        return 1

    print(f"\nWrote {len(STEPS)} figures to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
