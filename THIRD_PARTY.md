# Third-party components

The project LICENSE applies to original project code. It does not relicense downloaded dependencies or models. Preserve each dependency’s included license files.

| Component | Upstream source |
|---|---|
| llama.cpp | https://github.com/ggml-org/llama.cpp |
| whisper.cpp | https://github.com/ggml-org/whisper.cpp |
| llama2.c | https://github.com/karpathy/llama2.c |
| CMake | https://github.com/Kitware/CMake |
| jetson-inference and recursive submodules | https://github.com/dusty-nv/jetson-inference |

Runtime revisions are recorded in the build scripts and compatibility guide. Model repository names, immutable revisions and file hashes are recorded in `models.json`; consult each repository’s model card for its license and usage terms. No downloaded model weights are committed to this repository.
