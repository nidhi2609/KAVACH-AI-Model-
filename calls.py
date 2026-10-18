"""Call-session endpoints: the mobile app starts a session when a call begins, streams short
audio/text chunks, and gets a running risk score plus a one-time alert flag."""
import hmac
import json
import secrets
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

import db
from detector import analyze_conversation, level_for

router = APIRouter()
MAX_CHUNK = 5 * 1024 * 1024
ALERT_AT = 50


def current_device(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    dev, _, secret = authorization[7:].partition(".")
    with db.get_db() as c:
        row = c.execute("SELECT token_hash FROM devices WHERE id=?", (dev,)).fetchone()
    if not row or not hmac.compare_digest(row["token_hash"], db.hash_token(secret)):
        raise HTTPException(401, "Invalid token")
    return dev


class SessionIn(BaseModel):
    caller_number: Optional[str] = Field(default=None, max_length=25)
    store_text: bool = False


class TextIn(BaseModel):
    text: str = Field(..., max_length=5000)


class NumberIn(BaseModel):
    number: str = Field(..., max_length=25)
    category: Optional[str] = Field(default=None, max_length=40)


def _reports(c, number_hash):
    if not number_hash:
        return 0
    return c.execute("SELECT COUNT(*) FROM number_reports WHERE number_hash=?", (number_hash,)).fetchone()[0]


def _session(c, sid, dev, must_be_open=True):
    s = c.execute("SELECT * FROM sessions WHERE id=? AND device_id=?", (sid, dev)).fetchone()
    if not s:
        raise HTTPException(404, "Session not found")
    if must_be_open and s["ended_at"] is not None:
        raise HTTPException(409, "Session already ended")
    return s


def _ingest(sid, dev, text):
    text = (text or "").strip()
    with db.get_db() as c:
        s = _session(c, sid, dev)
        t = (s["transcript"] + " " + text).strip()[-db.MAX_TRANSCRIPT:] if text else s["transcript"]
        r = analyze_conversation(t)
        top = max(r["score"], s["max_score"])
        new_alert = r["score"] >= ALERT_AT and not s["alerted"]
        c.execute("UPDATE sessions SET transcript=?, updated_at=?, max_score=?, alerted=?, signals=? WHERE id=?",
                  (t, time.time(), top, 1 if (s["alerted"] or new_alert) else 0,
                   json.dumps([i["label"] for i in r["indicators"]]), sid))
        reports = _reports(c, s["caller_hash"])
    return {"score": r["score"], "max_score": top, "level": level_for(top), "indicators": r["indicators"],
            "alert": new_alert, "stop_now": r["score"] >= ALERT_AT, "number_reports": reports,
            "recommendations": r["recommendations"]}


@router.post("/devices")
def register_device():
    dev, secret = uuid.uuid4().hex, secrets.token_urlsafe(32)
    with db.get_db() as c:
        c.execute("INSERT INTO devices(id, token_hash, created_at) VALUES (?,?,?)", (dev, db.hash_token(secret), time.time()))
    return {"device_id": dev, "token": f"{dev}.{secret}"}


@router.post("/sessions")
def start_session(body: SessionIn, dev: str = Depends(current_device)):
    db.purge_stale()
    sid, now, nh = uuid.uuid4().hex, time.time(), db.hash_number(body.caller_number)
    with db.get_db() as c:
        c.execute("INSERT INTO sessions(id, device_id, started_at, updated_at, caller_hash, store_text) VALUES (?,?,?,?,?,?)",
                  (sid, dev, now, now, nh, 1 if body.store_text else 0))
        n = _reports(c, nh)
    return {"session_id": sid, "number_reports": n, "known_scam_number": n >= 3}


@router.post("/sessions/{sid}/text")
def session_text(sid: str, body: TextIn, dev: str = Depends(current_device)):
    return _ingest(sid, dev, body.text)


@router.post("/sessions/{sid}/audio")
async def session_audio(sid: str, file: UploadFile = File(...), language: str = Form("en"), dev: str = Depends(current_device)):
    with db.get_db() as c:
        _session(c, sid, dev)
    if language not in {"en", "hi", "auto"}:
        raise HTTPException(422, "language must be en, hi or auto")
    data = await file.read(MAX_CHUNK + 1)
    if not data or len(data) > MAX_CHUNK:
        raise HTTPException(422 if not data else 413, "Audio chunk empty or larger than 5 MB")
    try:
        from transcriber import transcribe_audio
        text = transcribe_audio(data, file.filename or "chunk.wav", None if language == "auto" else language)
    except Exception as exc:
        raise HTTPException(500, f"Transcription failed: {type(exc).__name__}")
    out = _ingest(sid, dev, text)
    out["transcript_chunk"] = text
    return out


@router.post("/sessions/{sid}/end")
def end_session(sid: str, dev: str = Depends(current_device)):
    with db.get_db() as c:
        s = _session(c, sid, dev)
        now = time.time()
        c.execute("UPDATE sessions SET ended_at=?, transcript=CASE WHEN store_text=1 THEN transcript ELSE '' END WHERE id=?", (now, sid))
    return {"max_score": s["max_score"], "level": level_for(s["max_score"]), "signals": json.loads(s["signals"]),
            "duration_seconds": round(now - s["started_at"]), "text_stored": bool(s["store_text"])}


@router.get("/history")
def history(limit: int = 30, dev: str = Depends(current_device)):
    limit = max(1, min(limit, 100))
    with db.get_db() as c:
        rows = c.execute("SELECT id, started_at, ended_at, max_score, signals FROM sessions "
                         "WHERE device_id=? AND ended_at IS NOT NULL ORDER BY started_at DESC LIMIT ?", (dev, limit)).fetchall()
    return [{"session_id": r["id"], "started_at": r["started_at"], "duration_seconds": round(r["ended_at"] - r["started_at"]),
             "max_score": r["max_score"], "level": level_for(r["max_score"]), "signals": json.loads(r["signals"])} for r in rows]


@router.post("/numbers/report")
def report_number(body: NumberIn, dev: str = Depends(current_device)):
    nh = db.hash_number(body.number)
    if not nh:
        raise HTTPException(422, "Enter a valid phone number")
    with db.get_db() as c:
        c.execute("INSERT OR IGNORE INTO number_reports(number_hash, device_id, category, created_at) VALUES (?,?,?,?)",
                  (nh, dev, body.category, time.time()))
        n = _reports(c, nh)
    return {"number_reports": n, "known_scam_number": n >= 3}


@router.post("/numbers/lookup")
def lookup_number(body: NumberIn, dev: str = Depends(current_device)):
    nh = db.hash_number(body.number)
    if not nh:
        raise HTTPException(422, "Enter a valid phone number")
    with db.get_db() as c:
        n = _reports(c, nh)
    return {"number_reports": n, "known_scam_number": n >= 3}


@router.delete("/me")
def delete_me(dev: str = Depends(current_device)):
    with db.get_db() as c:
        c.execute("DELETE FROM devices WHERE id=?", (dev,))
    return {"deleted": True}
