# Kavach AI — Scam Conversation Shield

A prototype that combines phrase-based scam-signal detection with local Whisper speech-to-text for English, Hindi, and some Roman Hinglish. It supports typed text, audio upload, short microphone recordings, and browser-microphone live monitoring.

## Important limitations
- This is an awareness prototype, not a certified fraud detector. A low score does not mean a conversation is safe.
- Browser microphone capture is **not direct phone-call audio access**. For speakerphone calls, put the phone near the computer microphone and test in a quiet room. It may not separate the two speakers.
- Hindi speech is usually transcribed in Devanagari. Whisper may not preserve Roman Hinglish spelling. Typed Roman Hinglish is analyzed separately by the phrase rules.
- Live microphone requires localhost or HTTPS. Some deployed networks need a TURN server; STUN-only may fail behind restrictive NAT/firewalls.
- First run downloads the Whisper model and needs internet. CPU inference may be slower. Set `KAVACH_WHISPER_MODEL=base` for lower memory/faster but less accurate transcription, or `small` for a better general compromise.

## Run on Windows (PowerShell)

```powershell
cd path\to\kavach_ai_fixed
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Open the localhost URL Streamlit prints. Allow microphone permission in the browser. If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass` in that terminal and activate again.

## Test phrase detector

```powershell
pytest -q
```

## Deployment

Deploy the folder to a Python hosting service that supports Streamlit/WebRTC, set the start command to `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT` if supported by that platform, and make sure the public URL uses HTTPS. WebRTC deployments may require a reachable TURN relay configured through `KAVACH_TURN_URL`, `KAVACH_TURN_USER`, and `KAVACH_TURN_PASS`. Never commit credentials or `.streamlit/secrets.toml`.

A typical free CPU deployment can struggle with live speech inference or model downloads. Test the deployed microphone path separately from text detection. For a stable public app, consider a small always-on CPU service or hosted speech-to-text API, with explicit consent and privacy disclosure.

## Risk scoring
The score adds fixed points for configured phrase groups. It is not an ML confidence score and cannot determine whether a caller is truly a scammer. Confirm claims through official contact details and never share OTP/PINs or transfer money under pressure.
