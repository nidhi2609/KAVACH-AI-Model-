from fastapi.testclient import TestClient
from api import app

c = TestClient(app)


def test_health():
    assert c.get("/health").json()["status"] == "ok"


def test_analyze_scam_and_empty():
    r = c.post("/analyze", json={"text": "Aap abhi digitally arrest ho, paise transfer karo turant"})
    assert r.status_code == 200 and r.json()["score"] >= 50
    assert c.post("/analyze", json={"text": "  "}).status_code == 422


def test_check_link():
    r = c.post("/check-link", json={"text": "Update KYC http://sbi-kyc-update.xyz/login"})
    assert r.json()["links"][0]["score"] >= 60


def test_transcribe_validation():
    assert c.post("/transcribe", files={"file": ("a.wav", b"")}).status_code == 422
    assert c.post("/transcribe", files={"file": ("a.wav", b"x")}, data={"language": "xx"}).status_code == 422
