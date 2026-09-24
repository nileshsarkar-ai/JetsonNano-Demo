# Jetson Nano Demo browser portal

A light-themed, public text chat portal. Inference uses the JarvisLabs hosted `glm-5.3-flash` API; it does not run on the Nano or the hosting A30. This is separate from the repository's local Nano demos and has no camera access.

Create `/home/nano-demo/access.json` with an `api_key` key, mode 600. Never commit this file. Start `python3 app.py`; the default listening port is 6006. `DEMO_CONFIG` and `PORT` override configuration location and port. No sign-in is required. Anyone with the URL can use the demo and incur API usage.

Serve behind HTTPS. The API key stays on the server. Requests are bounded to 12 history messages, 40 KB payloads, three concurrent upstream calls and 4096 generated tokens. Inference and hosting incur usage charges. Stop the process when no longer needed; provider instance lifecycle is managed separately.

## Camera Lab

Open the HTTPS portal in Chromium **on the Jetson**, expand Camera Lab, choose Open camera, and allow camera permission. Choose a camera and experiment, then Analyze frame. Start live analysis repeats a snapshot after each response plus a 1-second pause; it is periodic image analysis, not continuous video understanding. Stop camera releases the camera; hiding the tab also stops it. No microphone is requested.

The browser uses cameras exposed by its operating system. USB webcams usually expose a browser-compatible video device; a CSI camera may require a system camera bridge and is not guaranteed to appear. Opening the portal on another computer uses that computer's camera, not the Jetson's.

Preview remains in the browser. Explicit analysis sends a JPEG snapshot (maximum 480 pixels wide) to the server and hosted model API. The application does not save frames. Modes: Quick scene labels (people, objects and actions), Scene scientist, Read and explain, Invent with objects, Robot planner. Robot planner only describes hypothetical steps; it cannot control hardware.

Deployment verification: public image endpoint returned a description of the supplied board photograph. Actual Jetson camera capture remains to be verified on that device.
