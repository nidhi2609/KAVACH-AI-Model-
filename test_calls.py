import time

import db
from fastapi.testclient import TestClient
from api import app

c = TestClient(app)


def new_device():
    return {"Authorization": "Bearer " + c.post("/devices").json()["token"]}


def test_auth_required():
    assert c.post("/sessions", json={}).status_code == 401
    assert c.post("/sessions", json={}, headers={"Authorization": "Bearer x.y"}).status_code == 401


def test_full_call_flow_and_privacy():
    h = new_device()
    sid = c.post("/sessions", json={"caller_number": "+91 98765 43210"}, headers=h).json()["session_id"]
    r1 = c.post(f"/sessions/{sid}/text", json={"text": "Hello, this is a normal call about your appointment."}, headers=h).json()
    assert r1["score"] == 0 and r1["alert"] is False
    r2 = c.post(f"/sessions/{sid}/text", json={"text": "I am from Crime Branch, you are under digital arrest. Do not tell anyone, transfer money now."}, headers=h).json()
    assert r2["alert"] is True and r2["stop_now"] is True and r2["score"] >= 50
    r3 = c.post(f"/sessions/{sid}/text", json={"text": "Send it quickly."}, headers=h).json()
    assert r3["alert"] is False  # alert fires only once
    end = c.post(f"/sessions/{sid}/end", headers=h).json()
    assert end["max_score"] >= 50 and end["text_stored"] is False
    assert c.post(f"/sessions/{sid}/text", json={"text": "x"}, headers=h).status_code == 409
    with db.get_db() as conn:
        assert conn.execute("SELECT transcript FROM sessions WHERE id=?", (sid,)).fetchone()[0] == ""
    hist = c.get("/history", headers=h).json()
    assert len(hist) == 1 and hist[0]["max_score"] >= 50


def test_devices_are_isolated_and_deletable():
    a, b = new_device(), new_device()
    sid = c.post("/sessions", json={}, headers=a).json()["session_id"]
    assert c.post(f"/sessions/{sid}/text", json={"text": "hi"}, headers=b).status_code == 404
    assert c.delete("/me", headers=a).json()["deleted"] is True
    assert c.get("/history", headers=a).status_code == 401


def test_number_reports_need_distinct_devices():
    for _ in range(3):
        assert c.post("/numbers/report", json={"number": "9876500001", "category": "digital arrest"}, headers=new_device()).status_code == 200
    h = new_device()
    r = c.post("/numbers/lookup", json={"number": "+91-98765-00001"}, headers=h).json()
    assert r["number_reports"] == 3 and r["known_scam_number"] is True
    assert c.post("/numbers/lookup", json={"number": "12"}, headers=h).status_code == 422
    one = new_device()
    for _ in range(3):
        c.post("/numbers/report", json={"number": "9876500002"}, headers=one)
    assert c.post("/numbers/lookup", json={"number": "9876500002"}, headers=one).json()["number_reports"] == 1


def test_stale_session_is_purged():
    h = new_device()
    sid = c.post("/sessions", json={}, headers=h).json()["session_id"]
    c.post(f"/sessions/{sid}/text", json={"text": "transfer money now"}, headers=h)
    with db.get_db() as conn:
        conn.execute("UPDATE sessions SET updated_at=? WHERE id=?", (time.time() - 7200, sid))
    c.post("/sessions", json={}, headers=h)  # starting any session triggers the purge
    with db.get_db() as conn:
        row = conn.execute("SELECT transcript, ended_at FROM sessions WHERE id=?", (sid,)).fetchone()
    assert row["transcript"] == "" and row["ended_at"] is not None
