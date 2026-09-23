# Nano setup and named experiments

For the original Nano 4GB, JetPack 4 / Ubuntu 18.04, system Python 3.6. Initial preparation needs Internet, sudo, cooling and disk space. Prepared inference is local.

```bash
git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git
cd JetsonNano-Demo
bash scripts/run_demo.sh
```

Already cloned? Run `git pull --ff-only` inside that folder, then the same Bash command.

1. Choose **1** to install/build the language runtimes and download checked models. Default setup excludes speech and training dependencies.
2. Choose **2** to inspect board resources and dependencies.
3. Select a [named experiment](EXPERIMENTS.md) directly. Start with **15 Mission Control**, **16 Document Detective**, or **17 Story Director**.
4. For a camera, first select **13**, then **install**. Rehearse **13 → detect** before choosing **18 Scene Memory**, **19 Visual Scavenger Hunt**, or **20 Change Journal**. USB uses `v4l2:///dev/video0`; an appropriate CSI camera may use `csi://0`.
5. New language demonstrations are **9**, **14**, and **22–28**. They need only the prepared language runtime.
6. Ctrl+C cancels a supervised demo; **0** exits. Run the Bash command again to return later.

The optional **21** sequence runs the original prepared text projects and tries a prepared USB camera. It does not run every experiment or replace rehearsal. Missing camera is reported and skipped.

The terminal-only video is an instructional command walkthrough, not footage of a successful Nano installation. It contains no desktop/background-window capture. Logs are in `runs/demo-*`; explicit assistant memory is in `runs/classroom-memory.json`. Use fictional classroom facts and clear them through experiment 9 when finished.
