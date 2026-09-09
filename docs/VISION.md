# Camera and TensorRT labs

Run the core setup first, then `JOBS=2 bash scripts/build_vision.sh` on the original Nano. JetPack must already include CUDA, TensorRT and multimedia components. This optional installation uses system packages and installs native bindings under /usr/local. The script disables upstream automatic pip/PyTorch installers. It does not install modern PyTorch.

Source is pinned to jetson-inference commit `45da40a8f3c180191b269f57f736caaa025b8a69`, with recursive submodules fixed by that commit. A fresh clone downloads these sources during vision setup. The original local copy also has `sources/jetson-inference.tar.gz`, which setup uses if present; the archive is not tracked in Git. The archive is created from Git objects to preserve case-sensitive Linux filenames even when saved on a Mac. Exact submodule revisions are in `sources/vision-revisions.txt`. Retain upstream licenses.

These bindings and camera paths have NOT been executed on a physical Nano. The pinned source explicitly includes CUDA SM53 and JetPack4 support; building successfully still depends on the installed image and packages. Stop the LLM server before starting vision to leave memory for TensorRT.

```bash
python3 labs/vision.py detect v4l2:///dev/video0 --input-width=640 --input-height=480
python3 labs/vision.py detect v4l2:///dev/video0 --speak
python3 labs/vision.py classify v4l2:///dev/video0
python3 labs/vision.py pose v4l2:///dev/video0 --threshold 0.15
python3 labs/vision.py segment v4l2:///dev/video0
python3 labs/vision.py detect /path/to/video.mp4 /path/to/results.mp4 --headless
python3 labs/vision.py detect csi://0 --input-width=640 --input-height=480
```

The first model load may download upstream vision weights and build a device-specific TensorRT engine. These optional vision weights are **not predownloaded in this package**. Internet is needed for that initial load. Keep `.vendor/jetson-inference/data/networks` and its generated engines on the Nano for subsequent offline sessions. Do not copy TensorRT engines from a different GPU/software stack. Record SHA-256 of downloaded weights and JetPack/TensorRT versions with your experiment; upstream model URLs are not immutable like the LLM manifest.

The code emits JSON records with object boxes/classes/confidences, image classifications, or detected people and a simple wrist-above-shoulder rule. Object count is occupancy per frame; it does not track identities or count unique visitors. The gesture rule is a geometric teaching example, not a trained sign-language recognizer. Talking camera uses detection labels plus eSpeak, not a vision-language model. Segmentation renders the class overlay. Network FPS excludes the full capture/render/audio pipeline.

The fetched upstream source (or local source archive) includes: Python examples, image collection tools, custom classification, SSD detection and segmentation training/export scripts. After extraction, see `.vendor/jetson-inference/python/examples` and `python/training`. Their training environments are separate from the dependency-free LLM scripts; read their included requirements before installation.

Reference: https://github.com/dusty-nv/jetson-inference/tree/45da40a8f3c180191b269f57f736caaa025b8a69
