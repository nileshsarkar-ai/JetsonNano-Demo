# JetsonNano-Demo

Three local AI demonstrations for the **original Jetson Nano 4GB**, with an optional camera. The reported board runs **Ubuntu 18.04.6 LTS**, with `python` **3.11.3** and `python3` **3.6.9**. Installation checks for **JetPack 4 / L4T R32** before making changes.

## Get started

```bash
git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git
cd JetsonNano-Demo
bash scripts/run_demo.sh
```

Already cloned:

```bash
cd JetsonNano-Demo
git pull --ff-only
bash scripts/run_demo.sh
```

The Bash command selects Python, checks the board and opens this menu:

| Choice | Action |
|---|---|
| 1 | Prepare selected models and dependencies |
| 2 | Board and dependency report |
| 3 | Text Conversation |
| 4 | Camera Object Detection |
| 5 | Camera-Guided Object Hunt |
| 6 | Storage Analyzer |
| 0 | Exit |

**Text Conversation** uses SmolLM2-360M Instruct Q4, a roughly **258 MiB** download. **Camera Object Detection** uses SSD-Mobilenet-v2 through JetPack's TensorRT stack. **Camera-Guided Object Hunt** shares those two models: the LLM proposes objects to find, and camera detections determine which have been found. This is a detector-plus-LLM application, not a trained VLA robot policy.

The default setup does not download the larger catalogue's extra models. Camera and language inference run sequentially. No paid API, external GPU, microphone or speaker is required.

## Check storage first

For a 32 GB card with about 4 GB free, inspect the board before choosing setup:

```bash
bash scripts/run_demo.sh --storage
bash scripts/run_demo.sh --check
```

The **Storage Analyzer**, also available as menu **6**, reports:

- Card/partition sizes, used/free space and inode usage.
- Large directories, ordered by size.
- Space grouped into model candidates, installed software/libraries, code/Git data, caches, logs, media and other files.
- The 30 largest individual files, with paths and allocated sizes.
- The 30 largest installed system packages.
- Existing model-file locations in the accessible home/repository directories.

The scan reads metadata and does not delete, move or load files. Categories use filename/path heuristics. Package figures overlap with file totals; do not add them together. Permission errors and time limits produce explicitly partial results. Other mounted filesystems, filesystem metadata and deleted-but-open files are not included in the root file inventory. A marketed 32 GB card is approximately 29.8 GiB before partition/filesystem overhead.

A **fresh runtime or camera-library build requires at least 6 GiB free**. Existing working runtimes can be reused; preparing the detector with installed camera bindings requires at least 1 GiB free headroom. These checks are minimum safeguards, not a guarantee of total build size. Unknown models found elsewhere are reported, not automatically adopted or deleted.

## Automatic setup

Choose **1**, or prepare without opening the interactive menu:

```bash
bash scripts/run_demo.sh --setup-only
```

Setup checks memory and disk, builds a missing language server, downloads/verifies the selected text model, checks native camera bindings, installs missing discovery tools, and prepares the detector. Camera preparation downloads weights and builds its device-specific TensorRT engine before camera demonstrations. Existing verified text weights and prepared camera assets are reused.

Initial preparation needs Internet and may request a sudo password. Sources, compiled runtimes and weights are downloaded/generated on the Nano rather than stored in Git. Once preparation succeeds, the demos use local assets. Text model downloads use pinned revisions and SHA-256 checksums; camera preparation receipts check cached file sizes, not cryptographic upstream provenance.

If camera preparation cannot finish, setup reports it and leaves the text demo available. A completed text setup does not certify camera readiness. Keep the `.vendor/`, `.tools/`, `models/` and `runs/` directories when reusing the installation.

## Python and system detection

The launcher prefers an installed **Python 3.11**, checking `python3.11`, `python`, then `python3`. If none is 3.11, it falls back to `python3` (minimum 3.6). It checks essential standard-library modules and never changes system Python symlinks.

JetPack camera extensions may require the system Python ABI. The launcher checks the selected interpreter and `/usr/bin/python3`, then runs camera code in the interpreter that can import the native bindings. To explicitly select system Python:

```bash
DEMO_PYTHON=/usr/bin/python3 bash scripts/run_demo.sh
```

`--check` reports Python paths/versions, OS, L4T, CUDA/TensorRT packages, power mode, swap, RAM, free disk, text dependencies, camera preparation and responding cameras. Detection does not change clocks, power mode, swap, CUDA or OS settings. The diagnostic command can run on an unsupported platform; installation remains restricted to the original Nano / L4T R32.

## Camera and demo controls

Camera discovery checks capture devices and attempts a frame with a timeout. It supports USB V4L2 devices and a detected CSI sensor through Argus; a manual URI or video path can be entered if automatic discovery misses the device. Discovery frames are not saved.

Keep the camera fixed for the object hunt. If no camera works, use Text Conversation. Model outputs and detector labels may be wrong; the object hunt scores detections rather than accepting an LLM's claim of success.

Ctrl+C cancels an active demo and returns to the menu. Session logs and generated outputs are saved under `runs/`. Resource checks, bounded execution and server cleanup reduce failure risk, but do not replace rehearsal on the actual board.

## Full catalogue and reference material

The previous catalogue remains available with its original option numbers:

```bash
bash scripts/run_demo.sh --all
```

Its setup prepares additional models and all four camera modes, so it needs more storage. The bundled RAG notes and evaluation prompts provide sample inputs. Historical speech/training code is outside the default three-demo setup.

- [Full experiment catalogue](docs/EXPERIMENTS.md)
- [Manual commands and historical workflows](docs/MANUAL-REFERENCE.md)
- [Camera implementation and setup](docs/VISION.md)
- [Compatibility notes](docs/COMPATIBILITY.md)
- [Validation record](docs/VALIDATION.md)
- [Presentation](docs/Jetson_Nano_Local_AI_Experiments.pptx) and [terminal walkthrough](docs/media/jetson-nano-setup.mp4)—these describe the earlier full menu; use the commands and compact menu above for the current default.

The software has regression tests for the launcher, interpreter selection, storage reporting and demo logic. CI includes Python 3.6, 3.9 and 3.11.3. These checks do not establish physical Nano, TensorRT or camera success.

## Repository layout

| Path | Contents |
|---|---|
| `scripts/run_demo.sh` | Interpreter selection and menu entry point |
| `scripts/demo_menu.py` | Compact and full menus, setup and supervision |
| `scripts/check_board.py` | System configuration report |
| `scripts/storage_report.py` | File, package and disk-space analysis |
| `scripts/readiness.py` | Dependency and camera checks |
| `models.json` | Pinned text model downloads and checksums |
| `config.json` | Runtime/client settings; compact menu selects the 360M model explicitly |
| `labs/` | Demo implementations |
| `data/` | Bundled sample inputs |
| `tests/` | Software regression tests |
| `runs/` | Generated logs, results and preparation receipts |

Project code is MIT licensed; see [LICENSE](LICENSE). Downloaded runtimes and models retain their upstream licenses: [THIRD_PARTY.md](THIRD_PARTY.md).
