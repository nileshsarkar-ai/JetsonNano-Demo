# Named Nano experiment menu

Use `bash scripts/run_demo.sh`. The [experiment list](EXPERIMENTS.md) is the current menu reference. Select **1** for core setup and **2** for board status. All 25 experiment entries have direct numbers and descriptive names; **21** optionally runs a prepared sequence. **0** exits.

## Hardware scope

Original Nano 4GB, JetPack 4 / Ubuntu 18.04, system Python 3.6. Only the camera is optional extra hardware. The active menu excludes speech, microphone/speaker interaction, external services and training. Earlier standalone audio/training scripts remain historical references.

Setup builds CPU language runtimes and downloads the default chat model, SmolLM2-360M Q4, and TinyStories 15M. It excludes Whisper by default. Camera installation is **13 → install** and needs a separate rehearsal because initial TensorRT engine compilation can take time. Use **13 → detect** before camera projects **18–20**.

## Supervision and recovery

- Checks available RAM, free disk and reported temperature before supervised work.
- Requires at least 768 MiB available RAM at start, with model-size headroom checks before loading.
- Stops monitored jobs below 256 MiB available RAM, below 256 MiB free disk, or at reported temperature 85°C or higher.
- Bounds child-process run time, captures command logs, and terminates owned process groups on timeout/cancellation.
- Stops the owned language server between selections and refuses to replace an existing server on its port.
- Serializes menu sessions using a file lock. Camera and language models run sequentially.
- Ctrl+C cancels a supervised activity and returns to the menu. Errors are shown rather than replaced by canned answers.

Installers inherit the real terminal for sudo. They are not killed by the runtime watchdog, to avoid interrupting package-manager state. Let package installation finish. Missing thermal sensors limit temperature monitoring. Sudden OOM, kernel failure or power loss cannot be prevented by a Python monitor.

Logs and structured outputs are stored in `runs/demo-*`. Experiment 9 stores explicit memory in `runs/classroom-memory.json` across sessions; choose its **clear** operation to remove those saved facts. Historical logs may still contain them. Use fictional examples in class.

## Rehearsal

Prepare while connected to the Internet, then test selected local demos on the physical Nano. Check output quality, power, cooling, actual camera capture and latency. The optional sequence skips an unavailable default USB camera; individual camera selections return an explicit error. These software safeguards do not establish flawless hardware operation.

These are classroom demonstration runners, not research execution infrastructure: they do not automatically provide W&B or durable off-machine backups for research jobs.
