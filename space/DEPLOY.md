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

## 4. Hardware & sleep (GPU cost)

The Space runs on **T4 small** (GPU) with a 15-minute idle auto-sleep. Manage via
the Space Settings UI or the API:

```python
from huggingface_hub import HfApi
api = HfApi(token="hf_...")
# change tier / sleep, or downgrade to free CPU:
api.request_space_hardware("cloudronin/uofa-demo", hardware="t4-small", sleep_time=900)
api.request_space_hardware("cloudronin/uofa-demo", hardware="cpu-basic")  # free, slow
api.pause_space("cloudronin/uofa-demo")                                   # stop billing
```

Notes:
- GPU bills per hour **while awake**; it auto-sleeps after `sleep_time` seconds idle.
- A longer `sleep_time` means fewer cold starts but more cost.
- CPU (`cpu-basic`) is free but extraction is far slower and may hit the
  pipeline's 12-min extract timeout — use GPU for real runs.

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
