# Chairman demo: one launcher, one demo at a time

Target: original Jetson Nano **4GB**, JetPack 4 / Ubuntu 18.04 / L4T R32, **system Python 3.6**. No pip installation is needed for the core menu. A stable power supply and cooling are essential.

After downloading the repository:

```bash
cd JetsonNano-Demo
bash scripts/run_demo.sh
```

For an existing clone, update first with `git pull --ff-only`. The launcher checks the board, then opens the menu immediately. It does not start an experiment automatically.

## Before the event

1. Select **1 — Prepare / repair core setup** with Internet connected. This installs system packages (sudo may ask for your password), builds pinned CPU runtimes with **one build job by default**, and downloads/verifies the configured small LLM, showcase SmolLM2-360M Q4, Whisper, and TinyStories 15M. Allow hours for first compilation and at least 6 GiB free disk headroom. Failed network downloads retry up to three times; wrong checksums fail visibly. Re-running preparation reuses verified downloads and builds.
2. Select **2 — Board / dependency / resource report**. Then use **S → tour** or **C** for the student projects. See [SHOWCASE.md](SHOWCASE.md). Resolve missing components. Optional camera dependencies and PyTorch are not required for core demos.
3. Rehearse **each selected demo on the actual Nano**, with the same camera, microphone, display, notes, and power supply used at the event. Check the actual generated answers, not just exit status.
4. For vision, use **U → 13 → install**, then run the intended camera mode once while online. This primes first-use model downloads and TensorRT engine compilation. PyTorch training uses a separately installed matching legacy wheel; never install external GPU requirements on the Nano.
5. During the event, open the same launcher and choose the prepared demo. No apt/build/download runs happen automatically when entering the menu. Verified cached core models are checked locally before use.

Preparation without opening the menu:

```bash
bash scripts/run_demo.sh --setup-only
```

Read-only board/resource report:

```bash
bash scripts/run_demo.sh --check
```

## Developer utility map

The main menu leads with **S** (offline projects) and **C** (camera projects). Options 3–14 below are inside **U**, not the main presentation menu.

| Option | Demonstration | What to prepare |
|---|---|---|
| 1 | Core preparation / retry | Internet, sudo, disk space |
| 2 | Board, resources, dependencies | No model execution |
| 3 | Interactive chat | Core setup; `/quit` returns to menu |
| 4 | Single question, short answer | Core setup |
| 5 | Token inspection | Core setup |
| 6 | Grounded JSON extraction | Short source text; model may fail the grounding check |
| 7 | Calculator | A simple binary arithmetic question |
| 8 | RAG: index, retrieve, ask | Your real UTF-8 notes; create index first; at most 5 MiB |
| 9 | Speech: say, transcribe, assistant | eSpeak / audio file / working ALSA microphone as applicable |
| 10 | TinyStories 15M | Core setup; no LLM server needed |
| 11 | CPU benchmark, one repetition | Core setup; no other model server |
| 12 | Evaluation | Your JSONL dataset with prompt strings; optional expected strings |
| 13 | Detect, classify, pose, segment, talking detection | Optional vision installation and working camera/video |
| 14 | Tiny CPU LoRA base/adapt/generate | Compatible PyTorch, real corpus, trusted checkpoints |
| 0 | Exit | Stops the server owned by this launcher |

External GPU LoRA/QLoRA cannot run on the original Nano. The menu points to the separate training documentation; it does not attempt incompatible installs. These are demonstration entry points, not a research experiment management system. Research protocols still require their own tracking, approval and preservation.

## Failure handling

- A Linux file lock prevents two instances of this menu from running simultaneously.
- Only one menu action runs at a time. The launcher refuses model demos when another service occupies the configured server port; it does not kill that service.
- The menu starts its own model server only for demos needing one, waits up to ten minutes for readiness, and stops it when that action finishes or fails. Stories, vision, benchmarks and training run without a retained LLM server.
- Monitored child processes run in their own process groups. Ctrl+C, an execution timeout, a failed server, or a resource guard stops the owned group, then returns to the menu. Termination escalates to SIGKILL after a bounded wait. Exiting the menu cleans up its server.
- Starting a monitored process requires at least 768 MiB available RAM. Model checks additionally require twice the model-file size plus 512 MiB headroom. These conservative estimates are **not** proofs of peak runtime memory use.
- During monitored execution, available RAM below 256 MiB, disk space below 256 MiB, or a reported thermal-zone temperature of at least 85°C stops the demo. Missing RAM telemetry blocks execution; missing thermal telemetry is shown as unavailable. The guard polls every 250 ms, and every second while loading the server.
- The menu rejects contexts above 1,024 tokens, batches above 64, or more than four CPU threads. Training uses batch size one on CPU; camera runs have explicit frame and time limits. Interactive chat/voice have no total-duration limit but retain resource checks.
- Input files are limited to 64 MiB in the menu. Finite demos have bounded durations. Logs and unique output paths live under `runs/demo-*`; per-command captured output logs are capped at 20 MiB. Server logs are separate. A failed action is recorded rather than replayed silently or replaced with a fabricated success.
- Package installers keep the real terminal so sudo works. **They are not killed by the RAM/temperature watchdog**, to avoid interrupting package-manager transactions. Optional vision installation also uses this installer path. Do these steps before the event; they are not live presentation actions.

## What still needs a real-board rehearsal

Software tests use dummy processes and mocked hardware/network responses. They do not establish Nano inference speed, model accuracy, TensorRT compatibility, audio/camera reliability, or immunity to sudden memory spikes, kernel OOM, power loss, SIGKILL of the launcher, overheating, or storage failures. A killed launcher cannot guarantee cleanup of every descendant. Do not advertise a flawless hardware demo until the intended sequence has passed on the actual board.

Recommended student rehearsal: **2 → S → tour → 0**, checking actual answers. Rehearse **C → memory / hunt / journal** separately before presenting camera projects. Speech and training are optional developer utilities. If a selection fails, read its log and resolve the cause before putting it in the chairman's sequence.
