"""Lead capture - append a minimal contact record to a private HF Dataset.

We store ONLY {email, timestamp, pack, x_of_n, weakener_count} - never any
evidence content. Write-failure policy (no silent loss, no punishing the user):

  1. Try the HF Dataset upload with a couple of retries + backoff.
  2. On exhaustion, DO NOT block the unlock - the user already did their part;
     `accepted` stays True so the deeper write-up unlocks anyway.
  3. To avoid silent loss, the lead is written to a fallback sink - a JSONL file
     if a path is writable, else a structured log line (a lead email is not
     evidence/payload, so this is consistent with the no-payload-logging rule).

Config via env (set as Space secrets at deploy):
  HF_DATASET_REPO   e.g. "your-org/uofa-leads"   (private dataset)
  HF_TOKEN          a write token
  LEAD_FALLBACK_PATH  optional JSONL path (default /tmp/uofa-leads-fallback.jsonl)
"""

from __future__ import annotations

import io
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

_log = logging.getLogger("uofa.space.leads")


@dataclass
class CaptureResult:
    accepted: bool   # True whenever the email was valid - the unlock proceeds
    sink: str        # "dataset" | "fallback" | "fallback-log" | "invalid"
    detail: str


def _valid_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]


def build_record(email: str, pack: str | None, summary: dict | None, *, now: str | None = None) -> dict:
    """Minimal lead record - no evidence content ever."""
    c = (summary or {}).get("completeness", {})
    return {
        "email": email,
        "timestamp": now or datetime.now(timezone.utc).isoformat(),
        "pack": pack,
        "x_of_n": f"{c.get('n_assessed')}/{c.get('n_expected')}" if c else None,
        "weakener_count": len((summary or {}).get("weakeners", [])),
    }


def _push_to_dataset(record: dict) -> None:
    """Upload one lead as a uniquely-named JSON file (avoids read-modify-write
    races). Raises if not configured or the upload fails."""
    repo = os.environ.get("HF_DATASET_REPO")
    token = os.environ.get("HF_TOKEN")
    if not repo or not token:
        raise RuntimeError("HF dataset not configured (HF_DATASET_REPO/HF_TOKEN unset)")

    from huggingface_hub import HfApi

    stamp = record["timestamp"].replace(":", "-")
    fname = f"leads/{stamp}-{abs(hash(record['email'])) % 10**8:08d}.json"
    HfApi(token=token).upload_file(
        path_or_fileobj=io.BytesIO(json.dumps(record).encode("utf-8")),
        path_in_repo=fname,
        repo_id=repo,
        repo_type="dataset",
    )


def _fallback_sink(record: dict) -> str:
    """Persist the lead locally; if even that fails, log it. Never raises."""
    line = json.dumps(record)
    path = os.environ.get("LEAD_FALLBACK_PATH", "/tmp/uofa-leads-fallback.jsonl")
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        return "fallback"
    except OSError:
        _log.warning("LEAD (fallback-log): %s", line)
        return "fallback-log"


def capture_lead(
    email: str,
    *,
    pack: str | None = None,
    summary: dict | None = None,
    retries: int = 2,
    sleep=time.sleep,
    push=None,
    fallback=None,
) -> CaptureResult:
    """Capture a lead. Returns a CaptureResult; never raises and never blocks
    the unlock on a sink failure."""
    email = (email or "").strip()
    if not _valid_email(email):
        return CaptureResult(accepted=False, sink="invalid", detail="invalid email")

    record = build_record(email, pack, summary)
    push = push or _push_to_dataset
    fallback = fallback or _fallback_sink

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            push(record)
            return CaptureResult(accepted=True, sink="dataset", detail="stored")
        except Exception as exc:  # noqa: BLE001 - any sink error falls through to fallback
            last_err = exc
            if attempt < retries:
                sleep(2 ** attempt)

    sink = fallback(record)
    return CaptureResult(accepted=True, sink=sink, detail=f"queued to fallback ({last_err})")
