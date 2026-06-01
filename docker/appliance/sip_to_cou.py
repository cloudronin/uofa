"""Map a signed SIP bundle → surrogate-pack JSON-LD (the v2 reader path).

A 3-line shim so the demo entrypoint stays shell. Mirrors harness/run_corpus.py:
re-verify + read the signed bundle, write the COU the surrogate pack checks.

    python sip_to_cou.py <bundle.json> <measurement.pub> <cou.jsonld>
"""

import json
import sys
from pathlib import Path

from uofa_cli.readers.sip_bundle_reader import read_sip_bundle

bundle_path, pubkey_path, out_path = (Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
doc = read_sip_bundle(bundle_path, measurement_pubkey=pubkey_path)
out_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
print(f"wrote COU: {out_path}")
