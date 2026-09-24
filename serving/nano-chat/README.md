# A30 browser demonstration

User-requested hosted inference demo, not a research benchmark or training run. One A30, browser chat on port 6006, SmolLM2-360M-Instruct FP16. The Nano uses the same base model quantized as GGUF Q4, so outputs and performance are not identical.

Set MODEL_REVISION to a resolved Hugging Face commit before launching. Install requirements in an isolated remote venv. Model weights download only onto the GPU instance. The app generates a local access.json with browser login credentials; never commit that file. Chat histories are session inputs, not saved by application code. Source is preserved in Git; remote disk holds reproducible model cache and operational logs. No checkpoints or training results are produced.
