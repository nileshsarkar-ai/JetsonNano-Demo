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

## Replacement instance 545719 — 13:50 IST

- Live portal: https://cfa1715457191.notebooksn.jarvislabs.net/
- Installed faster-whisper 1.2.1 and prepared tiny CPU/int8 model without restarting the server or W100 broadcast.
- Generated English audio sample “Hello” transcribed as “Hello.” in 1.47 seconds.
- Generated question transcribed as “What is 12 plus 15?” in 0.78 seconds; chat answered 27 in 1.45 seconds.
- Broadcast remained active during speech tests.
- Separate /assets/voice-test.html exposes voice controls for testing only; main portal retains Chat and Vision.
- Added 15-second microphone permission timeout, 30-second transcription timeout, and reset of disabled controls on Stop. JavaScript syntax and existing mocked voice controls passed. Mock tests do not establish acoustic input success.
- Actual browser microphone permission remains unverified; do not enable voice on the main portal until real microphone capture and wake-word flow pass.
