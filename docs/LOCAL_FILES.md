# What is saved locally

- All authored Python, shell, configuration and documentation files.
- The PowerPoint catalogue in `docs/Jetson_Nano_Modern_AI_Catalogue.pptx`.
- No downloaded model weights are bundled in `models/`. Use `scripts/download.py` to fetch models on demand; pinned revisions and checksums are in `models.json`.
- llama.cpp, whisper.cpp, llama2.c and CMake sources under `.vendor/`, with Git revision metadata and upstream licenses. Host-compiled binaries are excluded; compile on the Nano.
- Complete pinned jetson-inference source and recursive submodule source in `sources/jetson-inference.tar.gz`. Extract only on a case-sensitive Linux filesystem through the vision setup script. This archive includes upstream camera examples and custom-model training code.

This is not a fully offline operating-system installer. Ubuntu development packages, a matching optional PyTorch wheel, optional LLM weights, and first-use vision weights still require preparation/download. External LoRA/QLoRA requires its own modern GPU environment and base-model download. Once all components for a chosen lab are installed and cached, inference uses local files.

## GitHub checkout

The GitHub repository includes all authored scripts, guides, configuration, model manifests, source revision records and the presentation. `.vendor/`, downloaded weights, build products and the large vision source archive stay local and are ignored by Git. The runtime and vision build scripts fetch their pinned sources if absent, so a fresh clone does not depend on the original Mac folder.
