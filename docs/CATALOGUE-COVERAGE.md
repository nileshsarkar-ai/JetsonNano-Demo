# Presentation and menu coverage

Checked 2026-09-23 against all 28 slides of `Jetson_Nano_Modern_AI_Catalogue.pptx` and the original repository commit `1c3a2b3`. The presentation lists 72 **ideas**, not 72 implemented experiments. No original lab or training file has been removed. Code availability below does not establish successful execution on a physical Nano.

## One launcher

After cloning, run `bash scripts/run_demo.sh`. Choose **1** for core setup, **2** for diagnostics, then **S → tour**. The tour runs the tool assistant, document detective, and story director sequentially. It skips an unavailable optional camera. **C** offers the camera projects; **U** exposes the earlier labs. **0** exits. Ctrl+C stops the current supervised activity and returns to the menu.

## New student projects

| Menu | Project | Implementation |
|---|---|---|
| S → agent | Assistant selects validated read-only tools for board status, exhibit facts, and time | `labs/projects.py` |
| S → detective | Questions answered from visible retrieved exhibit passages | `labs/projects.py`, `labs/rag.py` |
| S → story | Audience chooses a setting and changes the generated story | `labs/projects.py` |
| C → memory | Compare camera observations and explain measured scene changes | `labs/camera_tasks.py` |
| C → hunt | Model proposes an object quest; detections determine its score | `labs/camera_tasks.py` |
| C → journal | Record successive observations and explain measured changes | `labs/camera_tasks.py` |

Camera projects require **U → 13 → install** and a working supported camera. They use object detections plus a text model, not a vision-language model. Camera and language models run sequentially to reduce memory pressure. A fixed camera is required for meaningful movement comparisons.

## Earlier code and presentation topics

| Earlier capability | Menu / code | PPT coverage and limits |
|---|---|---|
| Offline chat, prompting, conversation history | U → 3 or 4; `labs/chat.py` | 01, 06, 07, 12; prompts can illustrate classification/summarization (09, 11), but there are no dedicated scored labs for those tasks |
| TinyStories generation | U → 10; `labs/stories.py` | 03; sampling controls in CLI, not a complete 05 comparison suite |
| Token inspection | U → 5; `labs/inspect_tokens.py` | 04 |
| Constrained JSON extraction | U → 6; `labs/extract.py` | 08, 10 |
| Calculator tool assistant | U → 7; `labs/calculator.py` | 35 |
| Notes retrieval and grounded answers | U → 8; `labs/rag.py` | 31, 32, 34; lexical BM25, no semantic embeddings or vector comparison (30, 33) |
| Speech recognition, speech output, voice assistant | U → 9 → transcribe / say / assistant; `labs/speech.py` | 16, 20; English Whisper, eSpeak NG, push-to-talk. Microphone and audio output required for live assistant |
| Object detection, pretrained classification, pose, segmentation, talking detector | U → 13; `labs/vision.py` | 42, 45, 47, 48; pretrained classification is not custom-classifier training (43) |
| Tiny transformer and local LoRA teaching code | U → 14; `training/tiny_lora.py` | 52, 54; optional compatible PyTorch, tiny educational CPU model, not production LLM fine-tuning |
| External LoRA/QLoRA and export | `training/finetune_external.py`, `docs/TRAINING.md` | 55–57 workflow; separate modern Python/GPU environment, intentionally outside the Nano menu |
| Model benchmarking and configured inference | U → 11; `scripts/benchmark.py`, `scripts/serve.py`, `models.json` | Building blocks for 02, 63, 64, 66; manual model/config changes and measurements required, not completed comparisons |
| Prompt evaluation | U → 12; `labs/evaluate.py` | Partial 72: user-supplied JSONL, exact-match results, latency and runtime metadata; not an automatic scientific evaluation of all topics |
| New tool assistant | S → agent | 38 and limited 36/37: board telemetry and read-only predefined tools; no arbitrary hardware control |
| New document detective | S → detective | Illustrates 15, 31, 32, 41; grounding instructions do not guarantee factuality or reliable abstention |

## Catalogue ideas without dedicated implementations

13–14 (thinking modes, multilingual evaluation); 17–19 (streaming ASR and neural TTS/comparisons); 21–29 (wake words, VAD, device commands/control, audio understanding); 30/33 (semantic/vector retrieval); 39–40 (persistent personal memory, prompt-injection lab); 43–44 (custom training, identity tracking/crossing counts); 46 (gesture control); 49–51 (VLM, general image captioning, learned anomalies); 53 (classifier transfer learning); 58–62 (distillation, synthetic data, active learning, overfitting/forgetting comparisons); 65 (KV-cache experiment); 67–71 (speculative decoding, routing, remote comparison, energy measurement, voice-stage profiling).

Some ideas can be explored manually with existing primitives. That is not the same as an implemented, validated demonstration. Camera scene memory does not implement identity tracking or persistent conversational memory. The default English speech model does not provide multilingual evaluation. Energy measurement would require additional hardware.

## Verification boundary

Software regression CI passed 43 tests on Python 3.6.15 and 3.9 for commit `f20fed1`: [CI run](https://github.com/nileshsarkar-ai/JetsonNano-Demo/actions/runs/35878438927). Tests use mocks and small dummy processes; they do not download/run models or establish camera, CUDA, installation, memory safety, speed, or answer quality on your board. Rehearse each intended selection on the actual Nano before presenting. See [menu safeguards](DEMO-MENU.md) and [walkthrough](SETUP-WALKTHROUGH.md).
