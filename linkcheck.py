"""Offline link risk checker. It only inspects the address text and never opens the link."""
import re
from urllib.parse import urlparse

_TLDS = ("com|in|org|net|co|gov|edu|info|xyz|top|icu|click|vip|buzz|cfd|sbs|site|online|link|shop|live|app|apk|me|ly|cc|tk|ml|ga|cf|gq|rest")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"']+|\b(?:[a-z0-9-]+\.)+(?:" + _TLDS + r")\b(?:/[^\s<>\"']*)?", re.I)
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "cutt.ly", "is.gd", "rb.gy", "shorturl.at", "t.ly", "ow.ly"}
RISKY_TLDS = {"xyz", "top", "icu", "click", "vip", "buzz", "cfd", "sbs", "rest", "live", "site", "online", "link", "shop", "tk", "ml", "ga", "cf", "gq"}
BRANDS = ["sbi", "hdfc", "icici", "axis", "paytm", "phonepe", "gpay", "npci", "uidai", "incometax", "irctc", "cbi", "police", "aadhaar", "aadhar", "rbi", "kotak", "pnb", "fedex", "dhl", "amazon", "flipkart"]
OFFICIAL = {"sbi.co.in", "onlinesbi.sbi", "hdfcbank.com", "icicibank.com", "axisbank.com", "paytm.com", "phonepe.com", "npci.org.in", "uidai.gov.in",
            "incometax.gov.in", "irctc.co.in", "rbi.org.in", "kotak.com", "pnbindia.in", "fedex.com", "dhl.com", "amazon.in", "amazon.com", "flipkart.com"}
TWO_PART = {"co.in", "gov.in", "org.in", "nic.in", "net.in", "ac.in", "co.uk", "com.au"}
KEYWORDS = re.compile(r"login|verify|kyc|update|reward|refund|claim|prize|gift|bonus|suspend|unblock", re.I)


def find_links(text):
    found = []
    for m in URL_RE.finditer(text or ""):
        u = m.group(0).rstrip(".,;:!?)]}'\"")
        if u and u.lower() not in [x.lower() for x in found]:
            found.append(u)
    return found


def _registered(host):
    p = host.split(".")
    return ".".join(p[-3:]) if len(p) >= 3 and ".".join(p[-2:]) in TWO_PART else ".".join(p[-2:])


def check_url(url):
    raw = (url or "").strip()
    try:
        parsed = urlparse(raw if "://" in raw else "http://" + raw)
        host = (parsed.hostname or "").lower()
    except ValueError:
        host, parsed = "", None
    if not host or "." not in host:
        return {"url": raw, "host": host, "score": 0, "level": "Not a valid link", "reasons": []}
    reg = _registered(host)
    official = reg in OFFICIAL or host.endswith((".gov.in", ".nic.in"))
    tokens = set(re.split(r"[^a-z0-9]+", host))
    flags = []
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
        flags.append((40, "Uses a raw IP address instead of a website name"))
    if "@" in parsed.netloc:
        flags.append((30, "Contains '@', which can hide the real destination"))
    if host in SHORTENERS or reg in SHORTENERS:
        flags.append((30, "Shortened link: the real destination is hidden"))
    if "xn--" in host:
        flags.append((30, "Look-alike (punycode) characters in the domain"))
    if parsed.path.lower().endswith(".apk"):
        flags.append((50, "Downloads an Android app file (.apk) outside the Play Store"))
    if not official and any((b in tokens) if len(b) <= 4 else (b in host) for b in BRANDS):
        flags.append((45, "Uses a bank/government/brand name but is not its official domain"))
    if not official and re.search(r"(?:^|\.)(?:gov|nic)\.in(?:\.|$)", host):
        flags.append((45, "Imitates an Indian government address (gov.in / nic.in)"))
    if host.rsplit(".", 1)[-1] in RISKY_TLDS:
        flags.append((20, "Domain ending commonly abused in scams"))
    if host.count("-") >= 2 or len(host) > 40 or host.count(".") >= 4:
        flags.append((10, "Unusually long or complicated address"))
    if not official and KEYWORDS.search(host + parsed.path):
        flags.append((15, "Asks to login, verify, update KYC or claim a reward"))
    if raw.lower().startswith("http://"):
        flags.append((10, "Not encrypted (http, not https)"))
    score = min(sum(p for p, _ in flags), 100)
    level = "High risk" if score >= 60 else "Suspicious" if score >= 30 else "No red flags found"
    reasons = [w for _, w in flags] or (["Matches a known official domain"] if official else [])
    return {"url": raw, "host": host, "score": score, "level": level, "reasons": reasons}
