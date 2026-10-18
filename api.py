"""Kavach AI REST API (for the mobile app). Run: uvicorn api:app --host 0.0.0.0 --port 8000
Optional: set KAVACH_API_KEY to require an X-API-Key header. Content is never logged or stored."""
import os
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from detector import analyze_conversation, VERSION
from linkcheck import find_links, check_url
from calls import router as calls_router

MAX_AUDIO = 25 * 1024 * 1024
LANGS = {"en", "hi", "auto"}

app = FastAPI(title="Kavach AI API", version=VERSION)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("KAVACH_CORS", "*").split(","), allow_methods=["*"], allow_headers=["*"])

app.include_router(calls_router)


def auth(x_api_key: Optional[str] = Header(default=None)):
    key = os.getenv("KAVACH_API_KEY")
    if key and x_api_key != key:
        raise HTTPException(401, "Invalid or missing API key")


class TextIn(BaseModel):
    text: str = Field(..., max_length=10000)


@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION}


@app.post("/analyze", dependencies=[Depends(auth)])
def analyze(body: TextIn):
    if not body.text.strip():
        raise HTTPException(422, "Text is empty")
    r = analyze_conversation(body.text)
    r["disclaimer"] = "Heuristic score, not a probability or proof. Call 1930 if money was lost."
    return r


@app.post("/check-link", dependencies=[Depends(auth)])
def check_link(body: TextIn):
    links = find_links(body.text)
    return {"links": [check_url(u) for u in links[:10]]}


@app.post("/transcribe", dependencies=[Depends(auth)])
async def transcribe(file: UploadFile = File(...), language: str = Form("en"), analyze: bool = Form(True)):
    if language not in LANGS:
        raise HTTPException(422, "language must be en, hi or auto")
    data = await file.read(MAX_AUDIO + 1)
    if not data:
        raise HTTPException(422, "Audio file is empty")
    if len(data) > MAX_AUDIO:
        raise HTTPException(413, "Audio larger than 25 MB")
    try:
        from transcriber import transcribe_audio
        text = transcribe_audio(data, file.filename or "recording.wav", None if language == "auto" else language)
    except Exception as exc:
        raise HTTPException(500, f"Transcription failed: {type(exc).__name__}")
    out = {"transcript": text}
    if analyze and text.strip():
        out["analysis"] = analyze_conversation(text)
    return out