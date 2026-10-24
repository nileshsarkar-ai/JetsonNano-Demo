# Voice checks — 24 October 2026

Endpoint: https://0825ec5455951.notebooksn.jarvislabs.net/

- JavaScript syntax and Python compilation passed.
- Mocked browser control tests passed: empty-reply guard, synthesis callbacks, missing-language voice, recognition startup, transcript handling, permission error and Stop.
- English and Hindi generated replies reached Speaking → Finished speaking in the actual browser.
- Kannada generated reply reached Speaking → Finished speaking in the actual browser.
- All three public Wikimedia audio clips reached ended=true with no media error: English 1.103s, Kannada 2.136s, Hindi 1.309s.
- Actual microphone recognition returned permission denied. No successful acoustic transcription claimed. The browser/site microphone permission must be enabled before an end-to-end spoken-question test can pass.
- Speech playback event verification does not independently establish pronunciation quality. Recognition availability depends on browser/service; synthesis depends on installed voices.
- Samples and attribution indexed in voice-sample-sources.json. No microphone recordings were saved.
