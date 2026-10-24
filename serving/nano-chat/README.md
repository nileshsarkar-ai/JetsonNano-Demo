# Jetson Nano Demo browser portal

A light-themed, public text chat portal. Inference uses the JarvisLabs hosted `glm-5.3-flash` API; it does not run on the Nano or the hosting A30. This is separate from the repository's local Nano demos and has no camera access.

Create `/home/nano-demo/access.json` with an `api_key` key, mode 600. Never commit this file. Start `python3 app.py`; the default listening port is 6006. `DEMO_CONFIG` and `PORT` override configuration location and port. No sign-in is required. Anyone with the URL can use the demo and incur API usage.

Serve behind HTTPS. The API key stays on the server. Requests are bounded to 12 history messages, 40 KB payloads, three concurrent upstream calls and 4096 generated tokens. Inference and hosting incur usage charges. Stop the process when no longer needed; provider instance lifecycle is managed separately.

## Camera Lab

Open the HTTPS portal in Chromium **on the Jetson**, expand Camera Lab, choose Open camera, and allow camera permission. Choose a camera and experiment, then Analyze frame. Start live analysis repeats a snapshot after each response plus a 1-second pause; it is periodic image analysis, not continuous video understanding. Stop camera releases the camera; hiding the tab also stops it. No microphone is requested.

The browser uses cameras exposed by its operating system. USB webcams usually expose a browser-compatible video device; a CSI camera may require a system camera bridge and is not guaranteed to appear. Opening the portal on another computer uses that computer's camera, not the Jetson's.

Preview remains in the browser. Explicit analysis sends a JPEG snapshot (maximum 480 pixels wide) to the server and hosted model API. The application does not save frames. Modes: Quick scene labels (people, objects and actions), Scene scientist, Read and explain, Invent with objects, Robot planner. Robot planner only describes hypothetical steps; it cannot control hardware.

Deployment verification: public image endpoint returned a description of the supplied board photograph. Actual Jetson camera capture remains to be verified on that device.

## Current Q&A with web search

Enable “Search the web for current answers” before sending a question. Only the latest question is sent to the search service; the model receives up to five result snippets with numbered sources, and the portal renders clickable source links. This is snippet-based search, not full-page browsing. Dates and relevance still need judgment. A 22-second subprocess timeout bounds search; failures are surfaced explicitly instead of claiming current verification. External snippets are marked untrusted and cannot authorize tool actions. Install `python3 -m pip install -r requirements.txt` in the serving environment before starting. Camera analysis does not invoke search.

## Deployment restored — 24 October 2026

Previous instance 514929 was no longer present. Restored repository revision 5857b9f on A30 instance 545595 (IN2), with persistent serving environment `/home/nano-demo/venv` and app `/home/nano-demo/nano-chat/app.py`.

Portal: https://0825ec5455951.notebooksn.jarvislabs.net/

Verified public page HTTP 200, date response (Saturday, 24 October 2026), and news response with source links. Physical camera capture was not retested. Instance left running as requested; compute rate at restoration ₹38.88/hour plus storage and API usage. Configuration secret stays in `/home/nano-demo/access.json`, excluded from Git.

## Voice companion

Voice input uses browser SpeechRecognition where available; it requests microphone permission, writes a transcript into the message box, and requires Send before submitting. Select English, Hindi or Kannada for recognition/playback. Recognition depends on the browser's speech service; Chromium builds may expose the API without a working service. Spoken replies use installed browser/system voices; missing languages show an explicit message instead of using the wrong voice. Stop voice cancels recording/playback; hiding the tab stops them too. Auto-speak is opt-in. Browser speech services may process audio remotely.

Public test recordings from Wikimedia Commons are embedded with author/license attribution and linked source pages. They test playback; microphone recognition of speaker playback can be suppressed by echo cancellation. They are not a recognition accuracy benchmark. Run `node serving/nano-chat/checks/check_voice.cjs` from the repository root for mocked control-flow tests.
