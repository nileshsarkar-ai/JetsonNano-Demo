# Training and deployment

## Tiny ordinary LoRA on the Nano

This optional script requires a PyTorch build compatible with the board's Python and JetPack. PyTorch 1.10 is the legacy Python 3.6 route documented by NVIDIA. Install an appropriate wheel separately. Keep it out of the default inference setup.

Supply a real UTF-8 text corpus with enough characters for both the 90% training split and the 10% validation split. Stop the LLM server before training on a memory-constrained board.

```bash
python3 training/tiny_lora.py base --text /path/to/corpus.txt --output runs/base.pt
python3 training/tiny_lora.py generate --checkpoint runs/base.pt --prompt "The "
python3 training/tiny_lora.py adapt --checkpoint runs/base.pt --text /path/to/adaptation.txt --output runs/adapted.pt
python3 training/tiny_lora.py generate --checkpoint runs/adapted.pt --prompt "The "
```

Parameters are explicit CLI arguments: device, seed, steps, batch size, sequence length, hidden dimension, heads, layers, rank, and learning rate. Defaults are intentionally small: two layers, width 64, context 64, batch 4, rank 4, CPU. CUDA is opt-in with `--device cuda` and requires a working legacy CUDA-enabled PyTorch installation.

Base training disables LoRA updates and trains base parameters. Adaptation freezes the base and trains only the low-rank A/B matrices. B starts at zero, so initial adapters leave base outputs unchanged. The attention mask prevents access to future positions. There is no BF16, FlashAttention, PEFT dependency, or four-bit training in this script.

The base vocabulary comes from the base corpus. Adaptation text and generation prompts must use characters already present in that vocabulary. The checkpoint stores full model state, architecture, seed, data hash, PyTorch version, and training settings. Load only your own trusted checkpoints. The script does not implement resumable optimizer state.

Validation uses one fixed held-out batch for a lightweight progress signal. It is not a full validation metric. The ordered split may still contain related or repeated content. Use a proper held-out dataset for research claims. A tiny model trained for a few hundred steps will not become a useful general assistant.

## LoRA or QLoRA on a separate modern GPU

**Not for the original Nano.** Use Python 3.10/3.11 and a modern supported NVIDIA GPU. Install a CUDA-enabled PyTorch 2.6.0 build appropriate for that machine, then use a separate environment:

```bash
python3 -m venv .venv-external
source .venv-external/bin/activate
# Install the appropriate CUDA-enabled torch==2.6.0 build for this GPU first.
pip install -r training/requirements-external.txt
python training/finetune_external.py --method lora --train /path/to/train.jsonl --validation /path/to/validation.jsonl --output runs/smol-lora
```

Each real JSONL record must contain nonempty `prompt` and `response` strings. Validation must be a separate held-out set. The script rejects exact duplicates across the two files and examples that exceed the selected maximum length. It masks prompt and padding tokens in the training loss.

To demonstrate four-bit NF4 training:

```bash
python training/finetune_external.py --method qlora --train /path/to/train.jsonl --validation /path/to/validation.jsonl --output runs/smol-qlora
```

Both methods default to the same pinned SmolLM2-135M-Instruct base model for a controlled small experiment. The QLoRA option uses bitsandbytes on the external GPU. It does not enable QLoRA on Maxwell Nano.

## Merge and export

On the external machine, merge the adapter into a fresh full-precision copy of the same base revision:

```bash
python training/finetune_external.py --merge-adapter runs/smol-lora/adapter --output runs/smol-merged
```

Then use the pinned llama.cpp converter on the external machine. The converter requires modern Python and its documented dependencies. Install the converter's requirements in a **separate conversion environment** if they conflict with the training environment. The source revision is listed in `docs/COMPATIBILITY.md`.

```bash
python /path/to/pinned/llama.cpp/convert_hf_to_gguf.py runs/smol-merged --outfile runs/smol-adapted-f16.gguf --outtype f16
/path/to/pinned/llama.cpp/build/bin/llama-quantize runs/smol-adapted-f16.gguf runs/smol-adapted-q4.gguf Q4_K_M
```

Copy the resulting GGUF to the Nano and use:

```bash
python3 scripts/serve.py --model-file /path/to/smol-adapted-q4.gguf
```

Compare base and adapted models on the same held-out prompts, quantization, decoding settings, and Nano configuration. A lower training loss alone does not establish improved generalization.

The external-GPU training and merge/export pipeline was not executed on the development Mac. Its dependency and hardware requirements differ deliberately from the board-facing code.
