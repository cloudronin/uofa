# Stage 2 production launch — operator checklist

**Status:** ARMED PENDING two inputs: (1) the four API keys, (2) the gate-7 result from calibration v5. The author fires; the run is then unattended for ~5 days (June 13 – July 4 window). Budget envelope ~$262, hard stop at $400.

## A. One-time arming (before firing)

1. **Credentials.** Copy `dev/tools/scripts/judge.env.example` to `~/.uofa/judge.env`, fill the four keys, then `chmod 600 ~/.uofa/judge.env`. Judge C uses **`SAMBANOVA_API_KEY`** (not `HF_TOKEN`).
2. **Gate-7 path → prompt version.** After calibration v5, read `calibration-v5/gate7_result.md`. **PASS** → export `UOFA_PROMPT_VERSION=v1.2.0`; **RELAX** → leave the wrapper default `v1.1.0`. *(pending v5)*
3. **Smoke.** Verify all four providers (incl. Judge C via SambaNova): `bash dev/tools/scripts/smoke_full_panel.py` equivalent / the 2-case smoke. *(pending keys)*
4. **Keep the Mac awake** for the whole window: `sudo pmset -a sleep 0 disablesleep 1` (or run under `caffeinate -s`). Keep it powered and on the network the entire time — launchd does not wake a sleeping Mac or back-fill missed days.
5. **Install the LaunchAgent:**
   ```
   cp dev/tools/scripts/com.uofa.judge-daily.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.uofa.judge-daily.plist
   ```

## B. Fire Day 1

Start the first pass immediately rather than waiting for the 09:00 schedule:
```
UOFA_PROMPT_VERSION=<v1.2.0|v1.1.0> bash dev/tools/scripts/run_judge_daily.sh
```
launchd then re-runs it daily at 09:00 local; `--resume` makes each pass idempotent.

## C. The command the wrapper runs (reference)
```
uofa adversarial judge \
  --in dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz \
  --judges openai,gemini,hf-llama \
  --out dev/build/adversarial/phase3/production/run-1/ \
  --prompt-version <v> --concurrency 5 \
  --concurrency-per-judge "gemini=20,openai=10,hf-llama=10" \
  --max-requests-per-judge "gemini=950" --max-cost 400 --resume
```
Pin **one** prompt version for the whole run (a post-run drift guard exits non-zero on mismatch).

## D. Go / no-go (all true before firing)
- [ ] `~/.uofa/judge.env` present, `chmod 600`, all four keys set
- [ ] Smoke green on all four providers (Judge C via `SAMBANOVA_API_KEY`)
- [ ] `calibration-v5/gate7_result.md` exists; prompt version chosen (PASS=v1.2.0 / RELAX=v1.1.0)
- [ ] `GATE7_DECISION.md` written
- [ ] Resume-proof passed (kill mid-run, restart, no duplicate `case_id`s)
- [ ] Mac sleep disabled; powered and networked for the window
- [ ] LaunchAgent loaded
- [ ] Calibration v5 and Day-1 are on different UTC days (or Day-1 Gemini cap at 900) so they do not share the 1,000-RPD bucket

## E. Monitoring
`tail dev/build/adversarial/phase3/production/daily_status.log` → one line per run: `rc`, prompt version, spend to date, error count, per-judge case counts. Done when all judges reach ~4,556. Stage 3 triage and Stage 4 adjudication are out of scope here (resume on return); the low-confidence routing built in Part 3.1 is already wired into `uofa adversarial triage` (default on, threshold 0.5).

## Pending (need keys / v5)
- calibration v5 → `gate7_result.md` → `GATE7_DECISION.md`
- 2-case smoke + resume-proof
- final one-paragraph launch summary (judges, prompt version, gate-7 path, projected completion, projected spend)
