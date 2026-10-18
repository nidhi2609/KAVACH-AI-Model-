"""Local speech transcription using faster-whisper."""
import os
import tempfile
from pathlib import Path
from functools import lru_cache

# small is a better Hindi accuracy/speed compromise than base on most machines.
MODEL_SIZE = os.getenv("KAVACH_WHISPER_MODEL", "small")

@lru_cache(maxsize=1)
def _get_model():
    from faster_whisper import WhisperModel
    device = os.getenv("KAVACH_WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("KAVACH_WHISPER_COMPUTE", "int8" if device == "cpu" else "float16")
    return WhisperModel(MODEL_SIZE, device=device, compute_type=compute_type)

def transcribe_audio(audio_bytes, original_name="recording.wav", language=None):
    if not audio_bytes:
        raise ValueError("Audio file is empty.")
    suffix = Path(original_name or "recording.wav").suffix.lower()
    if suffix not in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}:
        suffix = ".wav"
    model, temp_path = _get_model(), None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(audio_bytes)
            temp_path = f.name
        segments, _ = model.transcribe(temp_path, language=language, beam_size=3, vad_filter=False, condition_on_previous_text=False)
        return " ".join(s.text.strip() for s in segments).strip()
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

def transcribe_array(audio, language=None):
    model = _get_model()
    segments, _ = model.transcribe(audio, language=language, beam_size=1, vad_filter=False, condition_on_previous_text=False)
    return " ".join(s.text.strip() for s in segments).strip()
