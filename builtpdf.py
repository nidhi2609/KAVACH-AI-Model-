from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, KeepTogether, PageBreak, ListFlowable, ListItem)

# ====== EDIT THESE THREE LINKS, THEN RE-RUN:  python build_pdf.py ======
LINKS = [
    ("1. Live Working Prototype", "https://YOUR-LIVE-APP-LINK-HERE", "Streamlit web app: text, audio, voice recording, link checker"),
    ("2. Demo Video", "https://YOUR-DEMO-VIDEO-LINK-HERE", "Explains the problem, the solution and a live walkthrough"),
    ("3. Source Code (GitHub)", "https://YOUR-GITHUB-REPO-LINK-HERE", "Full code, README, 42 automated tests"),
]
TEAM = "Team name: ____________________     Members: ____________________"
OUT = "/mnt/user-data/outputs/Kavach_AI_Prototype_Submission.pdf"
# ========================================================================

NAVY, BLUE, TEAL = colors.HexColor("#0b1f3a"), colors.HexColor("#2563eb"), colors.HexColor("#0891b2")
LIGHT, RED, GREY = colors.HexColor("#eef4fc"), colors.HexColor("#dc2626"), colors.HexColor("#475569")

H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=14, textColor=NAVY, spaceBefore=12, spaceAfter=5)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, textColor=BLUE, spaceBefore=6, spaceAfter=3)
B = ParagraphStyle("b", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=colors.HexColor("#1e293b"), alignment=TA_LEFT)
SM = ParagraphStyle("sm", parent=B, fontSize=8.5, leading=11.5, textColor=GREY)
CELL = ParagraphStyle("c", parent=B, fontSize=8.8, leading=11.8)
CELLB = ParagraphStyle("cb", parent=CELL, fontName="Helvetica-Bold")
TH = ParagraphStyle("th", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)
LNK = ParagraphStyle("l", parent=B, textColor=BLUE)

def P(t, s=B): return Paragraph(t, s)
def bullets(items, s=B):
    return ListFlowable([ListItem(P(i, s), leftIndent=12) for i in items], bulletType="bullet", start="\u2022", leftIndent=12, bulletFontSize=8)

def table(rows, widths, head=True, zebra=True):
    data = [[P(c, TH if (head and r == 0) else (CELLB if ci == 0 else CELL)) if isinstance(c, str) else c for ci, c in enumerate(row)] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]
    if head: st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0: st.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(st)); return t

def link_box():
    rows = []
    for name, url, desc in LINKS:
        rows.append([P(f"<b>{name}</b><br/><font size=8 color='#475569'>{desc}</font>", CELL),
                     P(f'<link href="{url}" color="#2563eb"><u>{url}</u></link>', CELL)])
    t = Table(rows, colWidths=[62 * mm, 112 * mm])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, BLUE), ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bfd3f2")),
                           ("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t

def on_page(c, d):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, A4[1] - 9 * mm, A4[0], 9 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 8.5)
    c.drawString(18 * mm, A4[1] - 6 * mm, "KAVACH AI  |  Hackathon Round 2  |  Prototype Submission")
    c.setFillColor(GREY); c.setFont("Helvetica", 8)
    c.drawString(18 * mm, 9 * mm, "Awareness prototype, not a certified fraud detector. India cyber-fraud helpline: 1930  |  cybercrime.gov.in")
    c.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {d.page}")
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=17 * mm, bottomMargin=16 * mm,
                      title="Kavach AI - Prototype Submission", author="Kavach AI Team")
doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=on_page)])
W = doc.width
S = []

# ---------- Title ----------
S += [Spacer(1, 4), P("Kavach AI", ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=28, textColor=NAVY, leading=32)),
      P("Anti-Digital-Arrest &amp; Scam Conversation Shield", ParagraphStyle("st", fontName="Helvetica-Bold", fontSize=13, textColor=TEAL, leading=17)),
      P("Prototype Requirements Document &mdash; Hackathon Round 2 Submission", SM), Spacer(1, 3), P(TEAM, SM), Spacer(1, 8),
      P("Working Links (all three)", H1), link_box(), Spacer(1, 3),
      P("Each link opens the prototype, the explanatory demo, and the code. Tap or click to open.", SM)]

# ---------- 1. Problem ----------
S += [P("1. The Problem", H1),
      P("Phone and video-call scams in India, especially <b>\"digital arrest\"</b> fraud, rely on <b>psychology, not hacking</b>. "
        "A caller poses as police, CBI, customs or a courier company, says the victim is under investigation (a drug parcel, money laundering, "
        "a linked Aadhaar), and keeps them on the line while demanding money or an OTP. Real agencies never arrest anyone over a call."),
      Spacer(1, 3),
      bullets(["<b>Victims panic and cannot think</b> in the moment: threat + secrecy + a deadline is designed to switch off judgement.",
               "<b>Existing tools miss it.</b> Spam-call blockers look at the number; antivirus looks at apps. Neither understands <i>what is being said</i>.",
               "<b>Language gap.</b> Scammers speak English, Hindi and Hinglish (Roman-script Hindi). Most tools work in English only.",
               "<b>The most vulnerable</b> (elderly, first-time digital users) need something simple, in their language, that gives a clear action: stop."])]

# ---------- 2. Solution ----------
S += [P("2. Our Solution and How It Solves the Problem", H1),
      P("Kavach AI listens to the <i>content</i> of a conversation (typed, uploaded audio or a voice recording), transcribes it locally when it is speech, "
        "and scores it against the <b>five classic scam-pressure tactics</b> plus credential theft. It then tells the user in plain language "
        "<b>why</b> it is suspicious and <b>what to do next</b>."),
      Spacer(1, 4),
      table([["Problem", "How Kavach AI addresses it"],
             ["Victim cannot judge in the moment", "Instant 0-100 risk gauge and a red <b>STOP</b> banner at score 50+, with the exact phrases highlighted in the text."],
             ["Tools ignore what is said", "Analyses the conversation itself: authority claims, threats, secrecy, urgency, money demands, OTP/PIN requests."],
             ["Hindi / Hinglish gap", "Rules handle English, Roman Hinglish and Devanagari Hindi; local Whisper speech-to-text supports Hindi and English."],
             ["No clear next step", "One-tap <b>Call 1930</b>, <b>Alert a family member</b> (WhatsApp pre-filled message), cybercrime.gov.in, and a downloadable report."],
             ["Scam links by SMS/WhatsApp", "Offline link checker flags fake bank/government domains, shorteners, IP links and .apk downloads without opening the link."],
             ["Privacy fears about call audio", "Local transcription, nothing logged, session text wiped when the call ends (see Section 6)."]],
            [48 * mm, W - 48 * mm])]

# ---------- 3. Features ----------
S += [P("3. Key Features and Functionality Demonstrated", H1),
      table([["Feature", "What it does in the prototype", "Source"],
             ["Text analysis", "Paste English / Hindi / Hinglish conversation. Ready-made samples (digital arrest, bank OTP, son in custody, normal call) for instant demo.", "app.py, detector.py"],
             ["Audio upload", "Upload wav/mp3/m4a/ogg/flac/webm, transcribe locally, edit the transcript, then analyse.", "app.py, transcriber.py"],
             ["Voice recording", "Record a short clip in the browser, transcribe and analyse it.", "app.py"],
             ["Explainable score", "Risk gauge, level (Lower signal / Caution / High / Very high suspicion), signals with points and the matched phrases highlighted.", "detector.py"],
             ["Smart negation", "\"Never share your OTP\" is treated as a <i>warning</i>, not a demand, so genuine bank advice is not flagged.", "detector.py"],
             ["Action buttons", "Call 1930, WhatsApp alert to family, cybercrime.gov.in, download .txt report.", "app.py"],
             ["Link checker", "Scores URLs 0-100 with reasons; lookalike gov.in domains are not trusted; link is never opened.", "linkcheck.py"],
             ["Learn tab", "Six common Indian scams (digital arrest, KYC, parcel, investment, QR/refund, relative in trouble) and the golden rule.", "app.py"],
             ["Accessibility", "Large-text toggle and Hindi UI toggle for elderly users.", "app.py"],
             ["REST API (for a mobile app)", "/analyze, /check-link, /transcribe, /health endpoints with optional API-key auth.", "api.py"],
             ["Live call-session API", "Anonymous device token, running score during a call, one-time alert, history, privacy-safe community number reports.", "calls.py, db.py"]],
            [32 * mm, W - 32 * mm - 33 * mm, 33 * mm])]

# ---------- 4. Demo ----------
S += [PageBreak(), P("4. Demo Walkthrough (what the video / live demo shows)", H1),
      P("Suggested 3-minute flow so the demo explains the <b>problem</b> and the <b>solution</b> end to end:", B), Spacer(1, 3),
      table([["Step", "Action", "What the judges see"],
             ["1 (0:00)", "State the problem in one line: \"Digital-arrest scammers keep victims on the line and pressure them into paying.\"", "Problem framing, Section 1"],
             ["2 (0:20)", "Text tab: click the <b>Digital arrest (Hinglish)</b> sample, press Analyze.", "Gauge near 100, STOP banner, five signals with highlighted phrases"],
             ["3 (0:50)", "Click <b>Normal call</b> sample.", "Score 0, green box: no false alarm"],
             ["4 (1:10)", "Record tab: say a scam line in English or Hindi; transcribe and analyse.", "Local speech-to-text feeding the same detector"],
             ["5 (1:50)", "Show the action buttons: Call 1930, Alert a family member, download report.", "Clear next step, not just a score"],
             ["6 (2:10)", "Link tab: paste <font face='Courier'>https://sbi-kyc-update.xyz/login</font>.", "High risk with reasons; official sbi.co.in scores 0"],
             ["7 (2:35)", "Mention the API and call-session privacy design; close with limitations.", "Path from prototype to a mobile product"]],
            [20 * mm, W - 20 * mm - 55 * mm, 55 * mm])]

# ---------- 5. Tech ----------
S += [P("5. Technology and Approach", H1),
      P("<b>Approach:</b> an <b>explainable, rule-based</b> detector, not a black box. Every point in the score maps to a named signal and visible evidence, "
        "which matters when advising a frightened person. Speech recognition is separated from detection, so any transcript source can feed the same engine."),
      Spacer(1, 5),
      table([["Layer", "Technology", "Role"],
             ["Frontend", "Streamlit (Python), custom CSS, mobile-responsive", "Five-tab UI: Text, Upload, Record, Link, Learn"],
             ["Detection engine", "Python regex rule sets, Unicode NFC normalisation", "Six signal groups across English, Hinglish, Devanagari; negation handling for warnings"],
             ["Speech-to-text", "faster-whisper (Whisper, default \"small\" model), int8 on CPU", "Local transcription of Hindi / English audio, no cloud call needed"],
             ["Link analysis", "Python, urllib; heuristics only", "Offline URL risk score; never fetches the URL"],
             ["Backend API", "FastAPI + Uvicorn, Pydantic validation, CORS", "REST endpoints for a mobile client; upload size limits (25 MB / 5 MB chunks)"],
             ["Storage", "SQLite (standard library), SHA-256 hashing", "Device tokens, call sessions, hashed number reports"],
             ["Quality", "pytest, FastAPI TestClient", "42 automated tests covering detector, links, API, and call sessions"]],
            [30 * mm, 66 * mm, W - 96 * mm]),
      Spacer(1, 6), P("Risk scoring (fixed points per signal group, capped at 100)", H2),
      table([["Signal group", "Points", "Example it catches"],
             ["Authority impersonation", "15", "\"I am Inspector ... from Crime Branch\", \"digital arrest\""],
             ["Arrest / legal / account-block threat", "25", "\"you will be arrested\", \"your son is in custody\", \"account will be blocked\""],
             ["Secrecy / stay on the call", "20", "\"do not tell your family\", \"do not disconnect\", \"kisi ko mat batana\""],
             ["Urgency / pressure", "15", "\"immediately\", \"turant\", \"within 30 minutes\""],
             ["Money-transfer demand", "25", "\"transfer money to a safe account\", \"paise transfer karo\""],
             ["OTP / PIN / password / remote-access request", "45", "\"OTP bhejo\", \"install AnyDesk\" (Roman, Devanagari and mixed spellings)"]],
            [62 * mm, 16 * mm, W - 78 * mm]),
      Spacer(1, 3),
      P("Levels: 0-24 Lower detected signal, 25-49 Caution, 50-74 High suspicion, 75-100 Very high suspicion. "
        "The score is a heuristic count of pressure tactics, <b>not a probability</b>, and the app says so on screen.", SM)]

# ---------- architecture ----------
arch = Table([[P("<b>Input</b><br/>Typed text<br/>Uploaded audio<br/>Mic recording<br/>Pasted link", CELL),
               P("<b>Speech-to-text</b><br/>faster-whisper<br/>(local, Hindi / English)", CELL),
               P("<b>Detection engine</b><br/>Rules + negation<br/>Score 0-100<br/>Evidence phrases", CELL),
               P("<b>Output</b><br/>Gauge + STOP banner<br/>Why it is risky<br/>Call 1930 / alert family<br/>Report download", CELL)]],
             colWidths=[W / 4] * 4)
arch.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, BLUE), ("INNERGRID", (0, 0), (-1, -1), 0.8, colors.white),
                          ("BACKGROUND", (0, 0), (0, 0), LIGHT), ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#dff3f8")),
                          ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#dde8fb")), ("BACKGROUND", (3, 0), (3, 0), colors.HexColor("#fde4e4")),
                          ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
S += [Spacer(1, 6), KeepTogether([P("System flow", H2), arch, Spacer(1, 2), P("Audio goes through speech-to-text first; typed text and links go straight to their analysers. The same engine also powers the REST API.", SM)])]

# ---------- 6. Privacy ----------
S += [P("6. Privacy and Responsible Design", H1),
      bullets(["<b>Local processing:</b> speech is transcribed on the machine running the app; no third-party speech service is used.",
               "<b>Transcripts are wiped</b> when a call session ends, and abandoned sessions are purged after one hour, unless the user explicitly opts in to store text.",
               "<b>Anonymous by design:</b> devices get a random token (stored only as a hash); no name, phone number or contact list is needed.",
               "<b>Phone numbers are never stored in the clear:</b> community scam-number reports use a salted SHA-256 hash, and a number is flagged only after <b>3 reports from distinct devices</b>, which blocks one person from falsely labelling a number.",
               "<b>Link checker never opens links</b>, so users cannot be exposed to a malicious page by checking it.",
               "<b>Honest framing:</b> every result carries a disclaimer that a low score does not prove safety."])]

# ---------- 7. Evidence ----------
S += [P("7. Validation", H1),
      P("The prototype ships with <b>42 automated tests, all passing</b>: 27 detector tests (real screenshot-based scam transcripts, garbled speech-to-text output, "
        "Hinglish and Devanagari variants, and <i>normal-speech false-positive checks</i>), 6 link-checker tests, 4 API tests and 5 call-session privacy/isolation tests. "
        "Run <font face='Courier'>pytest -q</font> to reproduce.")]

# ---------- 8. Limits / roadmap ----------
S += [P("8. Current Limitations and Next Steps", H1),
      table([["Prototype limitation (stated openly)", "Planned next step"],
             ["Rule-based: can miss new scripts or flag unusual normal speech; score is not a probability.", "Collect consented, anonymised examples to tune rules, then add an ML classifier alongside the rules."],
             ["Browser microphone cannot tap real phone-call audio; speakerphone near the device is needed.", "Native Android app using the existing call-session API for in-call, real-time alerts."],
             ["Whisper may write Hinglish in Devanagari; first run downloads the model.", "Hosted or on-device speech model for faster, lighter transcription."],
             ["Link check is offline and heuristic only.", "Add reputation feeds and the community-reported number database at scale."]],
            [W / 2, W / 2]),
      Spacer(1, 4),
      P("<b>Bottom line:</b> Kavach AI is a working, explainable first line of defence that turns \"something feels wrong\" into a clear, in-language "
        "instruction: <b>stop, do not pay, do not share an OTP, call 1930</b>. A production-ready system is not claimed; this prototype demonstrates the core idea end to end."),
      Spacer(1, 8), KeepTogether([P("Submission Links (repeated for convenience)", H2), link_box()])]

doc.build(S)
print("built", OUT)