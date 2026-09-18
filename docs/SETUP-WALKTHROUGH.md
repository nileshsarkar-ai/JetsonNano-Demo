# Nano setup walkthrough

These commands are for the **original Jetson Nano 4GB (2019), JetPack 4 / Ubuntu 18.04 / L4T R32**, using system Python 3.6. Run them in a terminal on the Nano. Git, Internet access, cooling and several GB of free disk space are required.

Run each step only after the previous one succeeds. The accompanying command video is instructional; it does not show actual execution on Nano hardware.

## 1. Clone

```bash
git clone https://github.com/nileshsarkar-ai/JetsonNano-Demo.git
cd JetsonNano-Demo
```

If already cloned, enter the existing folder and run `git pull --ff-only` instead.

After cloning, the easiest route is:

```bash
bash scripts/run_demo.sh
```

This performs steps 2–6 automatically in one terminal, opens chat, and stops its server when you exit. The manual steps below explain each stage; choose either the one-command route or the manual route.

## 2. Check the board

```bash
python3 --version
python3 scripts/check_board.py --strict
```

Stop if the check fails. Do not bypass it on a Mac, Orin, or unsupported OS.

## 3. Install packages and build

```bash
bash scripts/install_system.sh
JOBS=2 bash scripts/build_runtimes.sh
```

Enter the Nano's password if sudo requests it. The initial build may take a long time. If compilation exhausts memory, retry with `JOBS=1 bash scripts/build_runtimes.sh`. Keep the system Python and JetPack installation; do not install the external GPU training requirements on the Nano.

## 4. Download models

```bash
python3 scripts/download.py --list
python3 scripts/download.py smol135-q4 whisper-tiny-en stories15m
```

Wait for verified downloads.

## 5. Start the server in Terminal 1

```bash
python3 scripts/serve.py
```

Wait for the server to report that it is listening, then keep this terminal running.

## 6. Chat in Terminal 2

Replace the path below with the actual location of the cloned folder:

```bash
cd /path/to/JetsonNano-Demo
python3 labs/chat.py
```

Enter a question. `/reset` clears history; `/quit` exits chat.

After exiting chat, try:

```bash
python3 labs/calculator.py "Multiply 12 by 7."
python3 labs/stories.py --model stories15m --tokens 128
```

Inspect the output: tiny models may make mistakes. This does not establish model accuracy.

## 7. Stop and restart

Press Ctrl+C in Terminal 1 to stop the server. Next time, enter the repository folder in both terminals, run `python3 scripts/serve.py` in Terminal 1, wait for readiness, and run `python3 labs/chat.py` in Terminal 2. Setup and downloads need not be repeated.

Camera and training labs are separate optional steps; see the main README.
