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

        # The package control gets its own figure, and this step doubles as a
        # regression check.
        #
        # Its own figure because a full-page shot of a ~3,000px readout does not
        # show it, and the download is the whole point: the user leaves with an
        # artifact a third party can verify without trusting this site. A
        # chapter that claims that and shows no control is asserting it.
        #
        # A regression check because the control's absence is silent. In
        # September 2026 the deployed Space rendered a SIGNED readout, told the
        # reader to download the package below, and offered nothing -- no error
        # in the UI, no line in the container log (see
        # studies/inspector-live-verification-2026-09/). `wait_for` raises here
        # rather than writing a figure of a missing button, so a rerun of this
        # script after any UI or deploy change fails loudly on the one defect
        # that previously could only be found by a person clicking through.
        page.get_by_role("radio", name="Reviewer", exact=True).click()
        time.sleep(1)

        pack = page.get_by_role("button", name="Download UofA package")
        try:
            pack.wait_for(state="visible", timeout=30_000)
        except Exception:
            # Say which of the two things went wrong, with an artifact to look
            # at. A bare timeout here is indistinguishable between "the Space
            # served no package" (the defect this check exists for) and "this
            # script's selector is stale" (a defect in the check itself), and
            # guessing between them from a checkout is what cost an evening the
            # first time. Verified against gradio 6.24: DownloadButton renders
            # as <button>, and this selector matches it.
            hits = page.get_by_text("Download UofA package").count()
            signed = "Signed" in (page.locator("body").inner_text() or "")
            debug = OUT / "06-package-FAILED.png"
            page.screenshot(path=str(debug), full_page=True)
            raise SystemExit(
                "\nThe package control did not appear.\n"
                f"  control text found in the page: {hits}\n"
                f"  readout claims a signature:     {signed}\n\n"
                "  0 found + signed=True is THE regression: a signed readout\n"
                "    with no package. See studies/inspector-live-verification-2026-09/.\n"
                "  0 found + signed=False means the run was not signed at all;\n"
                "    check the Space's UOFA_ISSUER_SIGNING_KEY secret.\n"
                "  1 or more found means the control is present and this\n"
                "    selector missed it. Fix the script, not the Space.\n\n"
                f"  Full-page screenshot written to {debug}\n"
                "  Figures 01-05 were written and are usable; 06 was not.\n")

        pack.scroll_into_view_if_needed()
        time.sleep(0.5)
        # Viewport, not full page: the reader should see the control in place
        # among the reviewer's closing lines, at the size a user meets it.
        _shot(page, *STEPS[5], full_page=False)

        browser.close()

    print(f"\nWrote {len(STEPS)} figures to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
