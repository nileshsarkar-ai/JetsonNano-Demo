# Validation status

The active scope is original Nano 4GB, JetPack 4 / Ubuntu 18.04, Python 3.6, optional camera. No physical Nano is connected in this development workspace.

The earlier code commit `f20fed1` passed 43 software regression tests on Python 3.6.15 and 3.9 in [CI](https://github.com/nileshsarkar-ai/JetsonNano-Demo/actions/runs/35878438927). The named-menu update passes 53 software tests locally, including route and local-text-experiment tests. These use mocked model responses and dummy child processes; no real inference, training or measured hardware experiments are part of the software tests.

Software checks cover input validation, bounded memory storage, actual-summary propagation, model-error propagation, sampling settings, per-condition logs, direct named routing, camera evidence rules, cancellation, process cleanup, timeout/resource checks and source checkout recovery. Bash syntax is checked separately.

Unverified on the physical board: package installation, pinned runtime compilation, TensorRT engines, camera capture, model quality, latency, temperatures and peak RAM. Resource monitoring reduces risk but cannot guarantee recovery from instantaneous OOM, power loss, kernel failure or an incompatible driver. Rehearse the exact selected demos on the board before presenting.

The updated command video is generated from terminal text only and decoded fully to check its media stream. It is instructional, not fabricated Nano execution.
