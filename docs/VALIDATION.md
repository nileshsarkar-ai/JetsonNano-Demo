# Validation record — 9 September 2026

## What actually ran

Development platform: macOS ARM64, native CPU builds. These observations are not Nano speed measurements or proof of Nano compatibility.

- Built the pinned llama.cpp server, CLI and benchmark, whisper.cpp main, and llama2.c with the host compiler. CUDA and Metal were disabled.
- Downloaded and verified SHA-256 for SmolLM2-135M-Instruct Q4_K_M, Whisper tiny.en, and TinyStories 15M against the immutable model manifest. Those three weights were subsequently removed at the user’s request; the download script can fetch them on demand.
- Served the real 135M GGUF on localhost. Chat and token counting returned actual model outputs. The test phrase `Jetson Nano 4GB` produced seven tokens.
- The calculator lab requested multiplication of 12 by 7, validated the generated operation, and computed 84.
- Extraction generated well-formed but invented values. The final script detected the absent source strings and exited nonzero. This is a deliberately visible quality failure.
- BM25 indexed real project documentation and returned scored passages. The 135M answer about CUDA was factually wrong despite retrieval. RAG is not treated as a guarantee of correctness. Use retrieve-only to inspect evidence, and compare larger models before classroom factual-answer tasks.
- Whisper tiny.en transcribed the pinned upstream `samples/jfk.wav` speech sample. This exercised file decoding, native recognition and transcript output; not microphone capture.
- llama2.c generated a short story with the real 15M checkpoint.
- The upstream llama-bench completed a 64-token prompt / 32-token generation workload. Its Mac timings are intentionally not presented as Nano performance.
- All board Python scripts were checked against Python 3.6 grammar; all setup shell scripts passed Bash syntax parsing. This does not substitute for executing them with the board interpreter.
- The strict board check correctly rejected the development Mac before any system installation.

## Not executed here

No physical Nano was connected. JetPack package installation, GCC8/Linux linking, CMake bootstrap on Nano, CUDA/TensorRT vision compilation, live camera/CSI capture, ALSA microphone capture, eSpeak playback, tiny PyTorch LoRA, external GPU QLoRA and GGUF conversion remain unverified execution paths. No claim is made that every catalogue topic is implemented or that every optional model has been tested.

## First run on the Nano

1. Run `python3 scripts/check_board.py --strict`; retain the report with experiments.
2. Run system installation and the CPU runtime build from the README. Run the model download commands to fetch and verify the required weights.
3. Start the server, try a short chat, then compare a prompt with known factual ground truth. Do not use a plausible answer as a correctness check.
4. Stop the server and run the benchmark. Use `tegrastats` in another terminal to observe actual memory, thermals and power mode.
5. Try a real recorded WAV before enabling the microphone voice loop.
6. Install the optional vision path separately, then use a camera or local video whose contents you can inspect. The first model load needs network access and engine compilation.
7. Only then attempt optional training with the matching PyTorch environment and a real corpus.

This package preserves model revisions, checksums, runtime commits, configurable seeds and parameters. Numerical results can still differ across architectures and library builds.

## Regression checks — 18 September 2026

Executed on macOS with Python 3.9.6, not on physical Nano hardware:

- Seven standard-library unittest checks passed: model listing, no-argument help, unknown-model rejection, empty-prompt rejection, literal single-prompt commands, lazy camera startup/end-of-stream using mocked bindings, and retrying an incomplete local Git checkout while preserving modified sources.
- All project Python files passed Python 3.6 grammar parsing. All shell scripts passed `bash -n`. This checks syntax, not execution under Python 3.6 or the Nano libraries.
- Camera startup follows the pinned jetson-utils lazy-open behavior: capture occurs before checking stream state, and end-of-stream exits the loop. Hardware validation remains required.
- Dependency checkout retries an empty, incomplete repository; existing wrong revisions or modified tracked source are rejected. Vision submodule downloads are retried on rerun.

Run the hardware-free regression suite with:

```bash
python3 -m unittest discover -s tests -v
```

The board scripts and regression suite retain Python 3.6 syntax and standard-library APIs. External GPU training retains its separate Python 3.10/3.11 environment.
