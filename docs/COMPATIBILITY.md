# Compatibility and implementation notes

## Intended device

Original Jetson Nano 4GB, ARM Cortex-A57 / Maxwell, compute capability 5.3, JetPack 4 / L4T R32. Recommended official baseline is the final JetPack 4.6.6 release. Ubuntu 18.04 commonly provides Python 3.6 and CMake 3.10. The default code avoids modern Python inference frameworks and CUDA entirely.

Newer Ubuntu community images may work but are not the validated target. Jetson Orin Nano is a different device. A CPU build is deliberate: this repository does not apply unsupported CUDA patches or modify NVIDIA headers to imitate BF16 support.

## Runtime pins

| Runtime | Release | Exact commit |
|---|---|---|
| llama.cpp | b5050 | `23106f94ea2bc3da929afb7330655fd5515d08dc` |
| whisper.cpp | v1.5.5 | `7395c70a748753e3800b63e3422a2b558a097c80` |
| llama2.c | pinned source | `350e04fe35433e6d2941dce5a1f53308f87058eb` |
| CMake, if needed | v3.22.6 | `0bfd4f1ed68180d3912386fb53d559b2a9e84b1b` |

The llama.cpp pin requires CMake >=3.14. The board script selects GCC/G++ 8 and ARMv8-A CPU code. It links `stdc++fs` for older libstdc++ filesystem support. The whisper.cpp pin uses C++11 and exposes the executable as `build/bin/main`, not newer releases' `whisper-cli` name.

The old runtime is a compatibility trade-off. It does not support every newer model architecture, and an old server can lack later security fixes. It binds to localhost only. Use trusted model sources. No public server deployment or GPU performance claim is part of this codebase.

## Python

The board-facing scripts use Python 3.6 grammar and standard-library APIs. They do not need Transformers, LangChain, llama-cpp-python, a vector database, NumPy, or pip. Tiny LoRA is an optional exception that requires PyTorch. Modern external training has a separate dependency file and Python version.

Installing a new interpreter does not update CUDA, the GPU architecture, system libraries, or compatible PyTorch wheels. Use an NVIDIA/community wheel that matches the installed JetPack and Python ABI if you choose local PyTorch. This project does not guess a wheel URL or install a desktop CUDA wheel on Jetson.

## Memory and correctness

- The 4GB is shared by OS, CPU, and GPU. Model file size is not peak working memory.
- Use one LLM server slot and short contexts. Four-bit inference is not QLoRA training.
- Start with the 135M model to establish execution, then compare 360M or Qwen 0.5B for quality.
- Model failures are expected research observations. JSON constraints enforce structure, not truth.
- RAG uses BM25 with basic Unicode word tokenization. It performs poorly when the query and notes use unrelated wording or languages without whitespace-separated words.
- Full prompts and generated answers can contain personal data. Results remain on the machine unless you explicitly copy them elsewhere.

## Complexity

For a fixed dense transformer, autoregressive inference depends on model size and context. KV-cache memory grows with retained context. The examples bound the context and output length instead of promising a specific token rate.

The educational BM25 implementation scans stored chunks. For C chunks, W total indexed words, and Q unique query terms, retrieval takes O(W + C*Q + C log C) time and O(W + C) working storage in the straightforward Python representation. It suits small corpora, not a large search service.

The tiny transformer uses dense causal attention, with attention work O(batch * layers * sequence_length^2 * hidden_dim). A LoRA update for a linear layer adds rank * (input_dim + output_dim) trainable parameters. Frozen base weights and intermediate activations still consume memory.

## Sources

- NVIDIA hardware: https://developer.nvidia.com/embedded/jetson-nano
- NVIDIA compute capability: https://developer.nvidia.com/cuda/gpus/legacy
- JetPack 4 end of life: https://forums.developer.nvidia.com/t/announcing-end-of-life-for-nvidia-jetpack-4-with-the-release-of-jetpack-4-6-6/314300
- JetPack libraries: https://developer.nvidia.com/embedded/jetpack-sdk-461
- Legacy PyTorch guidance: https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048
- Pinned llama.cpp API: https://github.com/ggml-org/llama.cpp/blob/23106f94ea2bc3da929afb7330655fd5515d08dc/examples/server/README.md
- Pinned whisper.cpp: https://github.com/ggml-org/whisper.cpp/tree/7395c70a748753e3800b63e3422a2b558a097c80
- TinyStories C runtime: https://github.com/karpathy/llama2.c
- LoRA: https://arxiv.org/abs/2106.09685
- QLoRA: https://arxiv.org/abs/2305.14314
- bitsandbytes requirements: https://huggingface.co/docs/bitsandbytes/installation
