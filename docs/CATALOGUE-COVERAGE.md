# Current presentation coverage

The current scope is the **Nano and optional camera only**, as requested on 2026-09-23. The active menu and `Jetson_Nano_Local_AI_Experiments.pptx` contain [25 named experiment entries](EXPERIMENTS.md), plus setup/report and an optional sequence. Each entry maps to executable code; no entry is a placeholder for external work.

The original `Jetson_Nano_Modern_AI_Catalogue.pptx` remains an archived 72-topic ideas reference. Its routes described feasibility, not implemented or tested demonstrations. It is not the current presentation programme.

## Code ownership

| Named entries | Implementation |
|---|---|
| 3–8: conversation, question, tokens, extraction, calculator, notes RAG | Original `labs/chat.py`, `inspect_tokens.py`, `extract.py`, `calculator.py`, `rag.py` |
| 9, 14, 22–28: memory, sampling, prompting, few-shot learning, triage, summary, injection, abstention, context | `labs/text_experiments.py` |
| 10: TinyStories | `labs/stories.py` |
| 11–12: benchmark and prompt evaluation | `scripts/benchmark.py`, `labs/evaluate.py` |
| 13: camera detection/classification/pose/segmentation | `labs/vision.py` |
| 15–17: tool assistant, document detective, story director | `labs/projects.py` |
| 18–20: scene memory, scavenger hunt, change journal | `labs/camera_tasks.py`, `labs/vision.py` |
| 21: optional prepared sequence | `scripts/demo_menu.py` |

## Deliberately outside the active programme

No external GPU or training workflows, microphone/speaker experiments, neural TTS, wake words, speech streaming, speaker recognition, GPIO peripherals, cloud APIs or power-meter experiments. Historical audio and training scripts are preserved as manual reference, but the menu does not call them and default setup does not install their dependencies.

The selected lightweight implementation also does not claim semantic embeddings, full VLM image understanding, learned visual anomaly detection, identity tracking, speculative decoding, or quantified CPU/GPU/energy comparisons. Some could be separate future porting projects; they are not silently labelled as available. Camera captions use detector evidence and a text model; retrieval uses BM25. Prompt defenses and model self-critique are teaching comparisons, not guarantees of reliability.

## Evidence boundary

Software tests use mocks and dummy processes. No physical Nano, camera performance, answer quality or end-to-end installation was verified in this workspace. The current slides and terminal-only walkthrough describe commands to execute, not measured results. See [validation](VALIDATION.md) and [menu safeguards](DEMO-MENU.md).
