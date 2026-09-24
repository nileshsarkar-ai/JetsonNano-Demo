# Jetson Nano Demo browser portal

A light-themed, password-protected text chat portal. Inference uses the JarvisLabs hosted `glm-5.3-flash` API; it does not run on the Nano or the hosting A30. This is separate from the repository's local Nano demos and has no camera access.

Create `/home/nano-demo/access.json` with `password` and `api_key` keys, mode 600. Never commit this file. Start `python3 app.py`; the default listening port is 6006. `DEMO_CONFIG` and `PORT` override configuration location and port. Browser login username is `demo`.

Serve behind HTTPS. The API key stays on the server. Requests are bounded to 12 history messages, 40 KB payloads, three concurrent upstream calls and 4096 generated tokens. Inference and hosting incur usage charges. Stop the process when no longer needed; provider instance lifecycle is managed separately.
