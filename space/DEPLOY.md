# Deploying the UofA Gap-Finder

The Gap-Finder is a Gradio app that runs as a **HuggingFace Docker Space**
([cloudronin/uofa-demo](https://huggingface.co/spaces/cloudronin/uofa-demo)) and
is embedded at **uofa.net/demo**.

Key fact: a HF Docker Space **builds the image itself** from the source you push
to the Space repo. Baking the ~3 GB model on HF's builder overran HF's
**30-minute build limit** ("Build error: Job timeout"), so the heavy image is
now **prebuilt in CI and pushed to GHCR** (`space/Dockerfile.base` →
`ghcr.io/cloudronin/uofa-demo-base`). What HF builds is a **thin** Dockerfile
(`FROM <base> + COPY space/`) that pulls the base and copies the app code —
finishing in ~2 minutes, comfortably inside the limit.

---

## 1. Continuous deployment (the normal path)

`.github/workflows/deploy-space.yml` deploys on every push to `main` that
touches `space/`, `src/`, `packs/`, `spec/`, `specs/`, `build-config/`,
`pyproject.toml`, or `keys/research.pub` (and on manual **Run workflow**).

It runs three jobs in order: (1) `pytest tests/space`; (2) **base** — build
`space/Dockerfile.base` and push `ghcr.io/cloudronin/uofa-demo-base:latest`
(registry-cached, so unchanged layers — including the 3 GB model — are restored,
not rebuilt); (3) **deploy** — sync the thin Space layout to `cloudronin/uofa-demo`
in one commit, which triggers HF's fast rebuild on the fresh base.

**Auth is keyless** — no `HF_TOKEN` secret in GitHub. The deploy job mints a
GitHub OIDC token (`permissions: id-token: write`) and exchanges it at
`https://huggingface.co/oauth/token` for a short-lived, repo-scoped HF token
(RFC 8693 token exchange). The base job pushes to GHCR with the built-in
`GITHUB_TOKEN` (`permissions: packages: write`) — also no extra secret.

### One-time: make the GHCR base image public

HF's builder pulls `ghcr.io/cloudronin/uofa-demo-base` **anonymously**, so after
the first `base` job pushes it, flip the package to public once: **GitHub →
Packages → `uofa-demo-base` → Package settings → Change visibility → Public**.
Until then, HF's build fails with `denied` / `failed to authorize` while pulling
the base — fix the visibility and re-run the Space build (**Factory rebuild**).

### One-time trusted-publisher setup (on the Space)

`spaces/cloudronin/uofa-demo` → **Settings → Trusted Publishers → GitHub
Actions**, with claims (matched exactly, no regex):

- `repository` = `cloudronin/uofa`
- `branch` = `main`
- `workflow` = `deploy-space.yml`

---

## 2. Manual deploy (fallback)

```bash
export HF_TOKEN=hf_...            # a token with write access to the Space
python space/deploy_to_hf.py      # syncs root Dockerfile + README + build context
```

`deploy_to_hf.py` assembles the Space layout (root `Dockerfile` = `space/Dockerfile`,
root `README.md` = `space/README.md`, plus the wheel build context) and commits
it in one shot. It **refuses to ship any `*.key`** and excludes caches/artifacts.

---

## 3. Lead capture (private HF Dataset)

Leads are appended to the private dataset **`cloudronin/uofa-leads`** by
`space/leadcapture.py`. The Space reads two **secrets** (Settings → Variables and
secrets):

- `HF_DATASET_REPO` = `cloudronin/uofa-leads`
- `HF_TOKEN` = a token with **write** access to that dataset

Capture degrades gracefully: if the dataset write fails, the user is still
unlocked and the lead falls back to a JSONL file / structured log (never lost).
The record contains only `{email, timestamp, pack, x_of_n, weakener_count}` —
never evidence content.

> **Least privilege:** prefer a **fine-grained, write-only token scoped to
> `cloudronin/uofa-leads`** (Settings → Access Tokens → Fine-grained) rather than
> a broad account token, and rotate it periodically.

---

## 3b. Package signing key (`UOFA_DEMO_SIGNING_KEY`)

The "Download UofA package" control signs each package with a **dedicated demo
issuer key**. Deliberately *not* `keys/research.key`: a demo artifact must never
be cryptographically indistinguishable from a research package, so the demo key
is its own identity and `uofa verify` requires `--pubkey keys/demo.pub`.

**Setup (one-time).** Generate the pair *outside the repo* and install the
private half as a Space secret:

```bash
uofa keygen ~/secure/uofa-demo.key     # writes uofa-demo.key + uofa-demo.pub
cp ~/secure/uofa-demo.pub keys/demo.pub   # public half is committed
```

Space → **Settings → Variables and secrets → New secret**:

| Name | Value |
|---|---|
| `UOFA_DEMO_SIGNING_KEY` | the full PEM contents of `uofa-demo.key` |

The PEM is read into memory at request time and never written to the container
filesystem — the process serves user downloads out of a temp directory, and a
private key on that filesystem is one path bug away from being one of them. For
local development, `UOFA_DEMO_SIGNING_KEY_FILE=/path/to/demo.key` works instead.

**The key can never travel as a file.** `space/deploy_to_hf.py` filters `.key`,
`.pem`, and `.env` out of the upload set *and* hard-refuses the deploy if one
survives (`_secrets_in`). The Space repo is public; treat anything committed
there as published.

**If the secret is unset** the Space still works: it degrades to the unsigned
readout it had before downloads existed, and the download button stays hidden.
That is the correct behaviour for a duplicated Space, which does not inherit
secrets.

**Rotating.** Generate a new pair, replace `keys/demo.pub`, update the secret,
and redeploy. Packages issued under the old key stop verifying against the new
`demo.pub` — which is the intended meaning of a rotation, not a regression.
Update the fingerprint published in `space/README.md`.

---

## 3c. Inference key (`TOGETHER_API_KEY`)

The Space carries no local model. Extraction is a hosted call configured by the
`UOFA_SPACE_LLM_*` vars in `space/Dockerfile.base`, which are **configuration
and live in git** so the model choice is reviewable and testable. Only the key
is a secret.

Space → **Settings → Variables and secrets → New secret**:

| Name | Value |
|---|---|
| `TOGETHER_API_KEY` | your Together AI API key |

The name is not hardcoded: `UOFA_SPACE_LLM_KEY_ENV` says which variable to read,
so pointing the Space at Fireworks, Groq, or a self-hosted vLLM is a Dockerfile
`ENV` change plus a differently-named secret. `openai-compatible` is the
protocol; the vendor is whatever `base_url` names.

**If the secret is missing** the Space does not crash and does not silently
produce nothing. `llm_env.missing_key_env()` detects declared-but-keyless and
the run fails as `FailureKind.NO_BACKEND`, naming the variable. That is exactly
the duplicated-Space case: HuggingFace copies the *declaration* to a duplicate
but never the *value*, so a duplicator sees a message telling them to add their
own key, rather than a generic extraction error they would retry forever.

**Duplicating the Space:** set your own `TOGETHER_API_KEY`, or set
`UOFA_SPACE_MODEL=mock` to explore the interface with canned data and no API
calls at all.

**Set a spend cap before going live.** See §4.

---

## 4. Hardware & sleep

**CPU is now the right tier.** The Space carries no local model: inference is a
hosted API call, so the GPU that existed to run qwen3.5:4b has nothing to do.

```python
from huggingface_hub import HfApi
api = HfApi(token="hf_...")
api.request_space_hardware("cloudronin/uofa-demo", hardware="cpu-basic")  # free
api.pause_space("cloudronin/uofa-demo")                                   # stop entirely
```

What actually changes, stated precisely, because it is easy to overclaim:

- **Sleep does not go away.** A free `cpu-basic` Space still sleeps, but on
  ~48 hours of inactivity rather than the 15 minutes configured for `t4-small`.
  For a demo visited sporadically that is the bigger practical win: it converts
  "almost always cold" into "almost always warm". Verify the current threshold
  against HF's docs before quoting it to a committee.
- **Waking gets much faster.** No GPU to schedule, an image roughly 1-1.5 GB
  instead of ~9-10 GB, and `start.sh` no longer blocks on loading 3 GB of
  weights before Gradio listens. Measure it rather than trusting this sentence:
  `curl -s -o /dev/null -w "%{time_total}\n" https://cloudronin-uofa-demo.hf.space/`
  after a forced pause, before and after.
- **True zero-sleep still needs paid hardware** (`cpu-upgrade` or above, where
  `sleep_time` becomes configurable). That is a separate budget decision. Going
  CPU-only makes it far cheaper than it was on GPU, so this change is a
  prerequisite for it rather than an alternative.

**Cost moves from idle time to use.** A T4 awake ~4 h/day costs roughly $70/month
whether or not anyone runs an analysis. Hosted inference is on the order of
$0.03-0.10 per analysis and $0 when idle. Confirm against Together's current
price list, and **set a spend cap before going live**: the Space is public, has
no rate limiting, and three preset example buttons are one click from a paid
call. The failure mode changed from "slow" to "expensive".

`DEFAULT_EXTRACT_TIMEOUT` stays at 720s. Its old rationale ("below Ollama's
30-min default") is stale, but it is now the ONLY effective bound on a hung
remote call: `LLMConfig.timeout_seconds` never applies here, because
`llm_extractor._call_llm` hardcodes `GenerationOptions(timeout_seconds=1800.0)`
and that always wins. It must also cover up to 3 retries and one call per file
when the corpus is chunked.

---

## 5. The uofa.net/demo embed

`site/src/components/GapFinderEmbed.astro` embeds the Space with a plain
**`<iframe>`** (NOT the `<gradio-app>` web component — see gotcha 4). The Space
host is `https://cloudronin-uofa-demo.hf.space`, overridable at site build time
via `PUBLIC_GAPFINDER_SPACE_ID`. The Space theme is tuned to the exact uofa.net
palette/fonts (`space/app.py` `THEME` + `CSS`, tokens from
`site/src/styles/custom.css`).

---

## 6. Verifying a deploy

```python
from huggingface_hub import HfApi
print(HfApi(token="hf_...").get_space_runtime("cloudronin/uofa-demo").stage)  # -> RUNNING
```

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://cloudronin-uofa-demo.hf.space/   # -> 200
```

Build logs (when a build fails): the GitHub run shows the sync; the HF **build
logs** are on the Space page (or `GET /api/spaces/cloudronin/uofa-demo/logs/build`
with a token — it's an SSE stream).

Then open uofa.net/demo (hard-refresh to bust the Pages CDN), or the Space
directly, and run **Try a sample evidence set** end to end.

---

## 7. Gotchas we hit (so you don't again)

1. **`build-config/` is required** for the wheel build (the hatch build hook
   `build-config/hatch_build.py`). Missing it → "Build script does not exist".
2. **`pkill -f "ollama serve"` self-terminates the build** — the build shell's
   own argv contains that string, so it SIGTERMs itself (exit 143). Kill the
   daemon by **captured PID** instead (see the Dockerfile).
3. **Model bake ordering (in `Dockerfile.base`):** the `ollama pull` layer sits
   **above** the wheel/pip layers, so a `src/` change (which rebuilds the wheel)
   re-runs only the cheap layers — the 3 GB model stays cached. The original
   single Dockerfile had this inverted (the bake sat *below* the wheel `COPY`), so
   every `src/` deploy re-pulled 3 GB and eventually overran HF's 30-min build
   limit → **Job timeout**. That's the whole reason the heavy build moved to CI +
   GHCR and the Space now builds only a thin `FROM <base>` image.
4. **Embed must be an `<iframe>`, not `<gradio-app>`.** The web component fetches
   `/config` from the parent page with `credentials:'include'`; HF's edge proxy
   omits `Access-Control-Allow-Credentials: true` on the cross-origin preflight
   for third-party domains → "could not get space status". An iframe loads the
   Space same-origin, sidestepping it.
5. **Theme:** the app is forced dark via `?__theme=dark`; the theme uses solid
   `#0c0d0e` surfaces (a transparent body renders white inside an iframe).
6. **Local image build:** Maven Central may be firewalled locally. The canonical
   `space/Dockerfile` builds fine on HF's networked builder; for a local build in
   a Maven-blocked network, inject the prebuilt jar and skip the Maven stage.
