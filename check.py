"""Run: python check.py   (same folder as app.py, same venv)"""
import sys, traceback
import importlib.metadata as md

print("Python:", sys.version)
for pkg in ["streamlit", "streamlit-webrtc", "faster-whisper", "av", "numpy", "twilio"]:
    try:
        print(f"{pkg}: {md.version(pkg)}")
    except Exception:
        print(f"{pkg}: NOT INSTALLED  <-- problem")

print("\n--- Test 1: detector ---")
try:
    from detector import analyze_conversation
    print("score:", analyze_conversation("Aap giraftar ho jaoge, abhi paise transfer karo")["score"])
except Exception:
    traceback.print_exc()

print("\n--- Test 2: Whisper model load (tiny, downloads ~75MB first time) ---")
try:
    from faster_whisper import WhisperModel
    import numpy as np
    m = WhisperModel("tiny", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(np.zeros(16000, dtype=np.float32), language="en")
    print("Whisper OK:", list(segs))
except Exception:
    traceback.print_exc()

print("\n--- Test 3: PyAV resampler ---")
try:
    import av, numpy as np
    r = av.AudioResampler(format="s16", layout="mono", rate=16000)
    fr = av.AudioFrame.from_ndarray(np.zeros((1, 960), dtype=np.int16), format="s16", layout="mono")
    fr.sample_rate = 48000
    out = r.resample(fr)
    print("Resampler OK:", out)
except Exception:
    traceback.print_exc()

print("\n--- Test 4: streamlit_webrtc import ---")
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    print("streamlit_webrtc import OK")
except Exception:
    traceback.print_exc()

print("\nDone. Copy ALL of this output and send it to me.")