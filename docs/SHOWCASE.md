> Menu update: use the [direct numbered experiment list](EXPERIMENTS.md). Older S/C/U shortcuts remain compatibility aliases; the main menu shows full experiment names.

# Student showcase: one Nano, local AI

These projects run on the original Jetson Nano 4GB / JetPack 4 / Python 3.6. **No cloud API, external GPU, microphone or speaker is required.** Internet is needed to prepare packages and model files, not for prepared text-project inference. The attached camera is optional. The terminal presents results; headless camera runs save video files instead of opening a display.

## Start here

```bash
git pull --ff-only
bash scripts/run_demo.sh
```

For a fresh clone, clone the repository and enter its directory first. Everything below is selected inside that same launcher:

1. **1 — Prepare** downloads/verifies the small models and builds the pinned runtimes. Do this before the class; it is not a live demo step.
2. **2 — Report** checks available resources and installed components.
3. **21 — Prepared sequence** runs the prepared offline projects automatically, then tries the optional camera journal only when `/dev/video0` and vision bindings are available. Camera failure is reported and skipped. Other failures stop the selection visibly and return to the main menu; there is no invented output or hidden replacement model.
4. **18–20** open the camera projects. For optional camera preparation, select **13 → install** once, then rehearse a capture. CSI cameras may need `csi://0` instead of `v4l2:///dev/video0`; enter the correct URI when prompted. The automatic tour probes only the default `/dev/video0` path.

## Projects and the learning point

| Project | What students see | What makes it more than a basic model call |
|---|---|---|
| **Mission control** | The LLM plans several read-only tools, executes them, then produces a briefing using exhibit facts and actual board memory | Structured planning, validated tool dispatch, live state, evidence-based synthesis. No generated shell execution. |
| **Document detective** | A question retrieves passages from a local document; the LLM answers with visible evidence | Retrieval and generation are separate; students can inspect sources and try questions the document cannot answer. |
| **Story director** | The model creates a scene, then incorporates an audience twist while retaining its earlier story | Multi-turn narrative context and interactive control. The automatic tour supplies a clearly printed example twist. |
| **Scene-memory detective** | Capture a desk, move/add/remove an object, then compare observations and explain the changes | Multi-frame consensus, temporal memory, count/position changes and grounded language generation. |
| **AI scavenger hunt** | The LLM creates a quest; students arrange real objects; the camera tracks progress over up to three rounds | Model-generated goals, constrained plans, perception-driven state and deterministic completion checks. |
| **Workspace-change journal** | Three observations form an event history; the model summarizes the recorded changes | Temporal evidence aggregation and memory, rather than one-frame recognition. The automatic tour leaves five-second gaps for changes. |

The document brief is labelled **fictional demonstration data**, not a real deployment. The language model can still misunderstand or invent facts; visible source/tool evidence lets students discuss that limitation. This is not a promise of ChatGPT-level answers or real-time speed.

## Camera evidence and memory use

Each observation processes five frames spaced at least 0.4 seconds apart. A class is retained only when present in a strict majority of frames. Position changes require a normalized center displacement of at least 0.15 and only apply when that class has one stable object in both observations. There is **no person identification or general multi-object identity tracking**. Keep the camera fixed; otherwise camera movement can be mistaken for object movement. Detector mistakes and occlusion can still create false changes.

A visual quest uses two or three distinct targets from `bottle`, `cup`, `book`, `cell phone`, `chair`, and `person`. Prepare ordinary visible items; no special electronics are required. The code, not the model, checks whether supported targets have been observed across rounds. This remains detector evidence, not independently verified ground truth.

The vision process exits before the LLM is loaded, and the LLM is stopped before another camera capture. Captures have a 120-second time limit; first-use TensorRT builds must be completed during preparation. Low memory, heat, timeout or unavailable hardware results in a visible stop/skip. No empty observation is converted into a made-up change story.

## Model and presentation limits

The main showcase uses pinned **SmolLM2-360M Instruct Q4**, already supported by the repository. It is approximately 258 MiB on disk; actual runtime memory is higher. It is intentionally small for the Nano's CPU and RAM. Output budgets stay short, with a 1,024-token context and one active LLM server. This is a capacity choice, **not a measured claim of Nano speed or answer quality**. The smaller chat lab has direct menu entry 3.

Software CI verifies the launcher and analysis logic under Python 3.6.15 and 3.9, using mocks/dummy processes. It does not execute models or establish camera compatibility. Before presenting, run the exact selected sequence on your board and inspect output quality and timing. If the camera is unavailable, the three text projects remain usable; audio and training demos are excluded from the active menu.

## Saved evidence

Session logs, resolved base configuration and command events are under `runs/demo-*`. Camera projects also retain raw capture logs, five-frame summaries, scene histories, quest plans and scores; headless captures save MP4 files. These local demonstration records are not automatic off-machine research backups or W&B experiments. Do not use this menu as a substitute for an approved research runner.

The full active programme also includes the nine local text experiments in [Named experiments](EXPERIMENTS.md).
