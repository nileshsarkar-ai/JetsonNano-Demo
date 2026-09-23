# JetsonNano-Demo

Runnable teaching code for the **original Jetson Nano 4GB (2019)** on **JetPack 4 / Ubuntu 18.04**. The board scripts use **Python 3.6+ and its standard library**. The default inference path uses native **CPU-only** C/C++ runtimes.

The student showcase includes an LLM tool-planning assistant, a document detective, an interactive story director, and camera projects for scene memory, visual scavenger hunts and change journals. Projects run sequentially on the Nano, with short local-model outputs and an optional camera. The active menu requires only the Nano and optional camera. Historical audio and training code remains in the repository for reference but is excluded from the menu and default setup. See [the showcase guide](docs/SHOWCASE.md).

**Validation boundary:** the pinned runtimes and real small models were exercised on the development Mac (ARM64 CPU). This is not a claim of testing on a physical Nano. See [docs/VALIDATION.md](docs/VALIDATION.md) for actual checks and remaining board checks.

## One-command demo menu

On the original Nano with JetPack 4 / Ubuntu 18.04 and system Python 3.6:

```bash
git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git
cd JetsonNano-Demo
bash scripts/run_demo.sh
```

Already cloned? Run `git pull --ff-only` inside the repository, then `bash scripts/run_demo.sh`.

The command opens a numbered experiment list with full names. Choose **1** to prepare before class, then select **15 Mission Control**, **16 Document Detective**, **17 Story Director**, **18 Scene Memory Detective**, **19 AI Visual Scavenger Hunt**, or **20 Camera Change Journal**. Earlier labs remain directly available as **3–14**, including **9 Persistent Memory Assistant** and **14 Sampling Playground**. **21** runs the prepared demonstrations sequentially and skips an unavailable optional camera. [Full experiment list](docs/EXPERIMENTS.md).

Prepared text projects need only the Nano: no external GPU, paid API, microphone or speaker. The showcase uses pinned SmolLM2-360M Q4 with short outputs; no real-time speed claim is made. Camera processing and LLM generation run sequentially to avoid loading both at once. The launcher includes memory/disk/thermal checks, timeouts, server cleanup and session logs. These reduce risk but do not replace a real-board rehearsal.

[Showcase projects and student sequence](docs/SHOWCASE.md) · [Menu safeguards](docs/DEMO-MENU.md) · [Setup commands](docs/SETUP-WALKTHROUGH.md) · [Walkthrough video](docs/media/jetson-nano-setup.mp4)

The sections below retain the original manual reference. Speech and training sections are historical optional workflows outside the current Nano-and-camera presentation. For the active demo list, use [Named experiments](docs/EXPERIMENTS.md).

## 1. Copy the code to the Nano

Clone the project **on the Nano**, or open your existing local project folder. For a fresh clone:

```bash
git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git
cd JetsonNano-Demo
python3 scripts/check_board.py --strict
bash scripts/install_system.sh
JOBS=2 bash scripts/build_runtimes.sh
```

The strict check requires an original Nano, Linux ARM64, and L4T R32. It rejects Orin and other platforms before installing anything. The installer uses the configured Ubuntu repositories. It does not upgrade Ubuntu, change system Python, replace CUDA, enable swap, or alter power settings.

The build uses GCC/G++ 8, targets ARMv8-A, and compiles the runtimes without CUDA. If CMake is older than 3.14, it builds a pinned CMake 3.22.6 privately under `.tools/`. That first build can take a long time. Allow several GB of free disk space. Reduce `JOBS=1` if compilation exhausts memory.

Setup fetches pinned runtime sources when they are not already cached locally. Model weights are downloaded on demand using `scripts/download.py`; no model weights or compiled binaries are tracked in Git. Internet access is needed for initial packages, sources and selected model downloads. Inference runs offline after setup. Use a stable power supply and cooling. A headless Nano leaves more memory available than a desktop session.

## 2. Download small models

```bash
python3 scripts/download.py --list
python3 scripts/download.py smol135-q4 smol360-q4 stories15m
```

Downloads use **exact Hugging Face revisions and SHA-256 checksums** in `models.json`. Partial downloads never replace verified files. Transient network failures retry at most three times. Checksum errors fail visibly; there are no hidden fallback models.

| Key | Model | Purpose |
|---|---|---|
| `smol135-q4`, `smol135-q8` | SmolLM2 135M Instruct | Fast initial experiments, quantization comparison |
| `smol360-q4`, `smol360-q8` | SmolLM2 360M Instruct | Larger small-model comparison |
| `qwen05-q4`, `qwen05-q8` | Qwen2.5 0.5B Instruct | Another instruction model |
| `whisper-tiny-en` | Whisper tiny.en | English speech recognition |
| `stories15m`, `stories42m`, `stories110m` | TinyStories models | Story generation with pure C |

SmolLM2 GGUFs come from the named community quantizer in the manifest. Qwen's GGUF comes from Qwen. Each upstream model retains its own license. The 135M model has limited instruction-following ability and may invent facts. Model fit in memory is not a promise of good answers or real-time response.

## 3. Start a local model

Terminal 1:

```bash
python3 scripts/serve.py
```

Defaults live in `config.json`: 135M Q4 model, 1,024-token context, four CPU threads, 64-token processing batches, and one server slot. The server binds to **127.0.0.1 only**. Keep it running while using the language-model labs. Wait until it reports that it is listening.

Terminal 2:

```bash
python3 labs/chat.py
python3 labs/chat.py --prompt "Explain what a language-model token is." --temperature 0 --max-tokens 64
python3 labs/inspect_tokens.py "Jetson Nano 4GB"
```

Use `/reset` to clear chat history and `/quit` to exit. The client counts actual prompt tokens, reserves space for the answer, and removes old complete turns when necessary. A single oversized request fails clearly instead of silently discarding its beginning.

To change model, stop the server with Ctrl+C, download the desired model, and restart:

```bash
python3 scripts/download.py qwen05-q4
python3 scripts/serve.py --model qwen05-q4
```

Only one LLM should run at a time on the board. Keep the server context and the client's `config.json` context consistent. `--model-file /path/to/adapted.gguf` accepts a locally exported model supported by the pinned runtime.

## 4. Structured output and a calculator tool

```bash
python3 labs/extract.py "NVIDIA released JetPack 4.6.6 in November 2024."
python3 labs/calculator.py "Multiply 12 by 7."
```

The extraction script requests bounded JSON arrays, parses the result, and checks that every extracted value appears verbatim in the source. A grounding failure gives a nonzero exit code. This catches invented values, but does not establish that every category or omission is correct. The tiny default model may fail this example: that is a model-quality result, not something the script conceals.

The calculator asks the model for one arithmetic operation, validates the operation and numeric bounds, then computes with Python operators. It never executes model-generated Python or shell commands. A valid tool call can still represent a misunderstood question.

## 5. RAG over your own notes

Copy real UTF-8 `.txt` or `.md` files into `data/notes/`, then:

```bash
python3 labs/rag.py index
python3 labs/rag.py ask "What does my document say about the experiment?" --retrieve-only
python3 labs/rag.py ask "What does my document say about the experiment?"
```

This is **lexical BM25 retrieval, not semantic embedding search**. It needs no vector database or Python ML dependencies. Defaults are 100-word chunks, 20-word overlap, and two retrieved passages. Retrieved text and source labels print before the answer. The script abstains when all lexical scores are zero. Nonzero similarity does not guarantee sufficient evidence.

For prompt-injection experiments, modify a copy of your notes and observe whether the model follows document instructions. The prompt tells the model to treat evidence as data, but that instruction is not a security guarantee. Plain text extraction from PDF/Word is outside this script.

## 6. Speech recognition and a voice loop

```bash
python3 labs/speech.py transcribe /path/to/recording.wav --output runs/transcript.txt
python3 labs/speech.py say "Hello from the Jetson Nano."
arecord -L
python3 labs/speech.py assistant --device default --seconds 5
```

The assistant records one utterance after you press Enter, transcribes it with Whisper, asks the running LLM, and speaks one short answer. It processes these stages sequentially. Use an ALSA capture device from `arecord -L` if `default` does not work. A USB microphone must support the requested 16kHz mono capture or an ALSA plug device must convert it.

**Speech output uses eSpeak NG**, a lightweight non-neural synthesizer. It is an intentional old-Ubuntu baseline. Piper/Kokoro installation and neural TTS are not implemented. The configured Whisper model and default transcription path are **English only**. This is push-to-talk, not wake-word detection, VAD, or streaming recognition. Whisper can generate text for silence/noise, so inspect the displayed transcript.

## 7. TinyStories without a server

```bash
python3 labs/stories.py --model stories15m --prompt "Once upon a time" --tokens 128
python3 scripts/download.py stories42m
python3 labs/stories.py --model stories42m --temperature 0.6 --seed 42
```

This uses the pinned `llama2.c` tokenizer and model format. `--tokens` controls the upstream program's total generation steps, which includes prompt processing. The upstream model context also limits generation. These are story models, not chat assistants.

## 8. Compare models and settings

Stop the LLM server before the upstream benchmark to avoid competing for memory:

```bash
python3 scripts/benchmark.py --model smol135-q4 --output runs/smol135-q4-bench.json
python3 scripts/download.py smol135-q8
python3 scripts/benchmark.py --model smol135-q8 --output runs/smol135-q8-bench.json
```

This benchmark measures upstream prompt-processing and token-generation workloads. It does not evaluate answer accuracy. Do not interpret development-Mac speed as Nano speed.

For your own task evaluation, prepare JSONL records containing a `prompt` string and optionally an `expected` string. Start the server and run:

```bash
python3 labs/evaluate.py /path/to/questions.jsonl --output runs/task-evaluation.jsonl
```

The result includes actual model responses, server timings, runtime/model metadata, configuration, and a dataset hash. Optional exact-match scoring only fits tasks with a single expected string. It is not a general measure of answer quality. Output files use exclusive creation so an old experiment is not overwritten.

## 9. Training and LoRA

See [docs/TRAINING.md](docs/TRAINING.md):

- `training/tiny_lora.py`: a small character transformer and ordinary LoRA using a compatible PyTorch installation. CPU is the default. This is separate from the dependency-free inference path.
- `training/finetune_external.py`: LoRA or QLoRA on a separate modern CUDA GPU, plus adapter merging for later GGUF conversion.

Do **not** install `training/requirements-external.txt` on the Nano. Current bitsandbytes CUDA QLoRA does not support the original Nano's CC 5.3 / CUDA 10.2 stack.

## Camera and vision

After core setup, follow [docs/VISION.md](docs/VISION.md):

```bash
JOBS=2 bash scripts/build_vision.sh
python3 labs/vision.py detect v4l2:///dev/video0
```

Detection, classification, segmentation, pose rules and talking-camera examples use the Nano’s legacy TensorRT stack. Vision weights download on first use.

## Layout

```text
config.json                Small-model and audio defaults
models.json                Immutable model revisions and checksums
scripts/                   Platform report, build, download, serve, benchmark
labs/                      Runnable inference demonstrations
training/                  Tiny local LoRA and external-GPU adaptation
docs/COMPATIBILITY.md       Version choices and technical limitations
docs/TRAINING.md            Training and deployment instructions
docs/VALIDATION.md          What was actually checked
.vendor/                   Downloaded upstream runtime sources (generated)
.tools/                    Private CMake installation if needed (generated)
models/                    Downloaded weights (generated)
runs/                      Your results and indexes (generated)
```

All paths derive from the project directory, so the board code does not contain the development Mac's absolute paths. Keep datasets, prompts, seeds, model revisions, and hardware settings with any reported experiment. Running the code does not prove a scientific hypothesis.

## Licensing

Original project code is MIT licensed; see [LICENSE](LICENSE). Downloaded runtimes and model weights retain their upstream licenses. See [THIRD_PARTY.md](THIRD_PARTY.md).

## Presentation coverage

The included PPT is a 72-topic idea catalogue. See [the checked presentation-to-code coverage guide](docs/CATALOGUE-COVERAGE.md) for all original menu entries, the six new projects, and topics that do not yet have implementations.

Current classroom presentation: [Nano Local AI Experiments](docs/Jetson_Nano_Local_AI_Experiments.pptx). The earlier 72-topic catalogue is an archived ideas reference, not the active demo programme.

Historical speech setup is now explicit opt-in: `WITH_AUDIO=1 bash scripts/install_system.sh`, `WITH_AUDIO=1 bash scripts/build_runtimes.sh`, then `python3 scripts/download.py whisper-tiny-en`. This is outside the current classroom scope.
