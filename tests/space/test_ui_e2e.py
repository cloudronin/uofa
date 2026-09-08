"""The whole workflow through a real browser, ending in a verified package.

Every other test in `tests/space` drives a handler, a renderer, or the pipeline
directly. Those are the right shape for what they check, and they were all green
on 2026-09-08 while the deployed result page printed a re-verification command
naming `keys/demo.pub`, a file the package does not contain. The pack was
correct, `VERIFY.txt` inside the zip was correct, and the string a human would
actually copy was wrong, because nothing joined the rendered page to the
artifact it describes.

This file joins them. It clicks what a reviewer clicks, downloads what they
download, and runs the command the page told them to run.

Two targets, and they catch different failures:

**Local (default).** The Gradio app in-process, the model stubbed, a throwaway
issuer key in a temp directory. Hermetic, no network, no provider spend. Catches
rendering and wiring defects such as the one above.

**Live (opt-in, `UOFA_E2E_LIVE=1`).** The deployed Space. Catches deployment
drift and missing configuration, which is the class that held CI-6 BLOCKED until
the Space's issuer key was set. It spends real provider credit and takes about a
minute, so it never runs by default.

Skips cleanly when playwright or its browser is absent, in the same spirit as
the Jena-gated tests. Install with:

    pip install playwright && playwright install chromium
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

sync_api = pytest.importorskip("playwright.sync_api",
                               reason="playwright not installed")
pytest.importorskip("gradio")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIVE_URL = os.environ.get("UOFA_E2E_LIVE_URL", "https://cloudronin-uofa-demo.hf.space")


@pytest.fixture(scope="session")
def browser():
    """Chromium, or a clean skip when the binary was never downloaded."""
    from playwright.sync_api import Error, sync_playwright

    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Error as exc:                                   # noqa: PERF203
            pytest.skip(f"chromium unavailable; run `playwright install "
                        f"chromium` ({str(exc)[:80]})")
        yield b
        b.close()


@pytest.fixture
def local_app(demo_key_env, monkeypatch):
    """The real Gradio app, in-process, with the model stubbed.

    `demo_key_env` supplies a throwaway issuer keypair in a temp directory and
    re-points the trust anchor at its public half, so signing is exercised for
    real without any committed or deployment key. `_MODEL = "mock"` keeps
    extraction deterministic and offline; conftest's autouse fixtures already
    strip any ambient provider credentials.

    Yields the base URL.
    """
    from space import app

    monkeypatch.setattr(app, "_MODEL", "mock")
    demo = app.build()
    demo.launch(prevent_thread_lock=True, share=False, quiet=True,
                inbrowser=False)
    try:
        yield demo.local_url.rstrip("/")
    finally:
        demo.close()


# ── the flow, shared by both targets ─────────────────────────


def _reach_confirm_step(page):
    """Sample -> confirm standard -> analyze. Stops ON the confirm step.

    Separate from `_run_workflow` because the confirm step's controls are gone
    once "See my gaps" is clicked, so a test that inspects them has to stop
    here.
    """
    page.get_by_role("button", name="Try a sample evidence set").click()
    page.get_by_role("button", name="Analyze evidence").wait_for(timeout=120_000)
    page.get_by_role("button", name="Analyze evidence").click()

    gaps = page.get_by_role("button", name="See my gaps")
    gaps.wait_for(timeout=180_000)
    return gaps


def _run_workflow(page, *, change_first_factor: bool = True) -> None:
    """Sample -> confirm standard -> optionally correct one factor -> results."""
    gaps = _reach_confirm_step(page)

    if change_first_factor:
        # The first factor's "not-assessed" option. Correcting exactly one is
        # what makes the corrected/extracted split observable in the package.
        page.get_by_role("radio", name="not-assessed").first.check()

    gaps.click()
    page.get_by_text("Indicative summary").first.wait_for(timeout=180_000)


def _packed_verify_command(page) -> str:
    """The command the page tells a reviewer to run, as rendered."""
    return page.locator("pre.ri-cmd").first.inner_text().strip()


# ── local, hermetic ──────────────────────────────────────────


def test_every_factor_status_radio_is_clickable(browser, local_app):
    """The confirm step must actually be editable, not merely rendered.

    On 2026-09-08 all 216 Space tests were green while the deployed tool
    rendered every factor radio as `disabled`. A reviewer could not correct a
    single status. The one surface the design reserves for human judgment was
    read-only, and nothing noticed, because every other test drives the handler
    BEHIND the radio and none of them clicks it.

    Cause: Gradio infers interactivity from whether a component is an input to
    some event. Each radio is an input to its own `.change()`, but that
    inference does not reach components constructed inside `@gr.render`, so
    `interactive=True` has to be stated outright.

    Removing that argument fails this test.
    """
    page = browser.new_page()
    try:
        page.goto(local_app, wait_until="load", timeout=120_000)
        _reach_confirm_step(page)

        radios = page.locator('input[type=radio][value="not-assessed"]')
        radios.first.wait_for(timeout=60_000)
        total = radios.count()
        disabled = page.locator(
            'input[type=radio][value="not-assessed"][disabled]').count()
    finally:
        page.close()

    assert total >= 13, f"expected one radio group per factor, found {total}"
    assert disabled == 0, (
        f"{disabled} of {total} factor radios are disabled. The confirm step is "
        "the only surface a human may correct, so a disabled radio makes the "
        "tool's central claim false."
    )



def test_the_signed_flow_ends_in_a_package_that_verifies(browser, local_app, tmp_path):
    """Click through, download, and run the exact command the page printed.

    This is the assertion the suite was missing. `test_pack_cli_roundtrip`
    already proves a web-produced pack verifies, but it builds that pack by
    calling the pipeline. Nothing checked that the command shown on screen is
    the one that works against the file the button hands you.
    """
    page = browser.new_page(accept_downloads=True)
    try:
        page.goto(local_app, wait_until="load", timeout=120_000)
        _run_workflow(page)

        assert "Signed (demo key)" in page.locator("body").inner_text(), (
            "the run produced no signature, so the download path is untested"
        )

        cmd = _packed_verify_command(page)

        with page.expect_download(timeout=120_000) as info:
            page.get_by_role("button", name="Download UofA package").click()
        zip_path = tmp_path / "pack.zip"
        info.value.save_as(zip_path)
    finally:
        page.close()

    out = tmp_path / "unpacked"
    with zipfile.ZipFile(zip_path) as zf:
        members = set(zf.namelist())
        zf.extractall(out)

    # Every path the printed command names must be in the zip. This is the
    # check that would have caught `keys/demo.pub`.
    for token in cmd.split():
        if "/" in token or token.endswith(".jsonld"):
            assert token in members, (
                f"the page printed `{cmd}`, but {token!r} is not in the "
                f"package. Members: {sorted(members)}"
            )

    argv = cmd.split()
    assert argv[:2] == ["uofa", "verify"], f"unexpected command: {cmd!r}"
    proc = subprocess.run([sys.executable, "-m", "uofa_cli", *argv[1:]],
                          cwd=out, capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"the command the page printed failed.\ncmd: {cmd}\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def test_the_corrected_factor_is_attributable_in_the_downloaded_package(
        browser, local_app, tmp_path):
    """One status moved in the UI must arrive as `corrected`, the rest as `extracted`.

    The human-boundary gate rests on this split, and until now it was only ever
    checked in-process. This drives it through the actual radio a reviewer
    clicks.
    """
    page = browser.new_page(accept_downloads=True)
    try:
        page.goto(local_app, wait_until="load", timeout=120_000)
        _run_workflow(page, change_first_factor=True)
        with page.expect_download(timeout=120_000) as info:
            page.get_by_role("button", name="Download UofA package").click()
        zip_path = tmp_path / "pack.zip"
        info.value.save_as(zip_path)
    finally:
        page.close()

    with zipfile.ZipFile(zip_path) as zf:
        doc = json.loads(zf.read("uofa.jsonld"))

    blob = json.dumps(doc)
    assert "corrected" in blob, (
        "a status was changed in the browser but nothing in the package is "
        "marked corrected"
    )
    assert "extracted" in blob, (
        "every status reads as human-corrected; the comparison that separates a "
        "moved status from an untouched one has been dropped"
    )


def test_an_unsigned_run_offers_no_download(browser, monkeypatch, tmp_path):
    """Without a key: no download control, and no command naming a packed key.

    The negative half. A run that cannot sign must decline to offer a package
    rather than offering an unsigned one, and its page must not print an
    instruction for a file the reader was never given. Deliberately does NOT
    request `demo_key_env`, so conftest strips any ambient key.
    """
    from space import app, pipeline

    monkeypatch.setattr(app, "_MODEL", "mock")
    demo = app.build()
    demo.launch(prevent_thread_lock=True, share=False, quiet=True,
                inbrowser=False)
    page = browser.new_page()
    try:
        page.goto(demo.local_url.rstrip("/"), wait_until="load", timeout=120_000)
        _run_workflow(page, change_first_factor=False)
        # Visibility, not a string search. Gradio embeds its whole component
        # config as JSON in the page, so every label is "present" in the HTML
        # whatever its visible state -- an earlier version of this assertion
        # matched that config and failed on a correctly hidden button.
        download_visible = page.get_by_role(
            "button", name="Download UofA package").is_visible()
        body = page.locator("body").inner_text()
    finally:
        page.close()
        demo.close()

    assert "Unverified (demo)" in body or "unsigned" in body.lower()
    assert not download_visible, "an unsigned run offered a package download"
    assert pipeline.PACK_MEMBER_PUBKEY not in body, (
        "the unsigned page names a packed key for a package it never produced"
    )


# ── live, opt-in ─────────────────────────────────────────────


@pytest.mark.skipif(os.environ.get("UOFA_E2E_LIVE") != "1",
                    reason="set UOFA_E2E_LIVE=1 to drive the deployed Space "
                           "(spends provider credit, ~1 min)")
def test_the_deployed_space_produces_a_verifiable_package(browser, tmp_path):
    """The deployment, not the code. Catches drift and missing configuration.

    This is the check that was impossible while CI-6 was BLOCKED: the Space had
    no issuer key, so it produced no package to verify. Gated rather than
    deleted, because "the deployed thing still works" is not answerable from a
    checkout.

    A failure here is a deployment finding, not a code defect, until the same
    flow is shown to pass locally.
    """
    page = browser.new_page(accept_downloads=True)
    try:
        page.goto(LIVE_URL, wait_until="load", timeout=180_000)
        _run_workflow(page, change_first_factor=False)

        html = page.content()
        if "Download UofA package" not in html:
            pytest.fail(
                "the deployed Space produced no downloadable package. If the "
                "page reads 'Unverified (demo)', its issuer signing key is not "
                "configured; that is deployment configuration, not code."
            )

        cmd = _packed_verify_command(page)
        with page.expect_download(timeout=180_000) as info:
            page.get_by_role("button", name="Download UofA package").click()
        zip_path = tmp_path / "live.zip"
        info.value.save_as(zip_path)
    finally:
        page.close()

    out = tmp_path / "unpacked"
    with zipfile.ZipFile(zip_path) as zf:
        members = set(zf.namelist())
        zf.extractall(out)

    for token in cmd.split():
        if "/" in token or token.endswith(".jsonld"):
            assert token in members, (
                f"the deployed page printed `{cmd}` but {token!r} is not in the "
                f"package it served. Members: {sorted(members)}"
            )

    argv = cmd.split()
    proc = subprocess.run([sys.executable, "-m", "uofa_cli", *argv[1:]],
                          cwd=out, capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"the deployed package failed the command its own page printed.\n"
        f"cmd: {cmd}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
