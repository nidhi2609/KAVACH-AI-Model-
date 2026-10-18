import html
import re
import hashlib
from datetime import datetime
from urllib.parse import quote

import streamlit as st
from detector import analyze_conversation, PATTERNS
from linkcheck import find_links, check_url

st.set_page_config(page_title="Kavach AI | Scam Shield", page_icon="🛡️", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at top right,#12305a 0,#07111f 45%,#050912 100%);color:#eef3fb}
.block-container{max-width:860px;padding-top:1rem;padding-bottom:3rem}
footer,#MainMenu{visibility:hidden}
.hero{padding:1.2rem 1.3rem;border:1px solid #2a4a74;border-radius:20px;background:linear-gradient(120deg,#146cff38,#16c7d722);margin-bottom:.8rem}
.hero h1{color:#fff;margin:0 0 .15rem 0;font-size:2rem;line-height:1.15}
.hero p{color:#cfe0f6;margin:0;font-size:.95rem}
.chips{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.6rem}
.chip{background:#0c1d33;border:1px solid #2a4a74;color:#bcd3f2;border-radius:999px;padding:.15rem .65rem;font-size:.78rem}
.disclaimer{background:#1a2438;border:1px solid #33466a;border-left:4px solid #f59e0b;border-radius:10px;padding:.55rem .8rem;color:#c8d4ea;font-size:.82rem;margin-bottom:.6rem}
.res{display:flex;align-items:center;gap:1.1rem;flex-wrap:wrap;background:#0c1a2d;border:1px solid var(--c);border-radius:18px;padding:1rem 1.2rem;margin:.6rem 0;box-shadow:0 0 28px -12px var(--c)}
.gauge{width:128px;height:128px;border-radius:50%;background:conic-gradient(var(--c) calc(var(--p)*1%),#1b2a44 0);display:grid;place-items:center;flex:none}
.gin{width:100px;height:100px;border-radius:50%;background:#0a1525;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1}
.gin b{font-size:2.2rem;color:#fff}.gin span{font-size:.75rem;color:#8ea6c8;margin-top:.15rem}
.lvl{font-size:1.45rem;font-weight:700;color:var(--c)}
.sub{color:#bcd0ea;font-size:.92rem;margin-top:.2rem;max-width:30rem}
.stopbox{background:#3a0f14;border:1px solid #ef4444;border-radius:14px;padding:.8rem 1rem;color:#ffd9d9;margin:.5rem 0;font-weight:600}
.sig{background:#0e1b2e;border:1px solid #243b5a;border-radius:14px;padding:.7rem .9rem;margin:.45rem 0}
.sig-h{display:flex;justify-content:space-between;gap:.5rem;font-weight:600;color:#fff}
.pts{background:#ef444422;color:#ff9b9b;border-radius:8px;padding:0 .5rem;font-size:.85rem;white-space:nowrap}
.ev{margin-top:.35rem;display:flex;flex-wrap:wrap;gap:.3rem}
.ev span{background:#16283f;border:1px solid #2b4568;color:#b9d2f3;border-radius:8px;padding:.08rem .5rem;font-size:.8rem}
.sec{font-weight:700;color:#dbe8fb;margin:.9rem 0 .2rem 0;font-size:1.02rem}
.tbox{background:#0b1626;border:1px solid #243b5a;border-radius:12px;padding:.7rem .9rem;color:#d3e1f5;font-size:.92rem;line-height:1.55;word-break:break-word}
.tbox mark{background:#ef444444;color:#fff;border-radius:4px;padding:0 .15rem}
.safe{background:#0f2a1f;border:1px solid #22c55e66;border-radius:12px;padding:.7rem .9rem;color:#c9f3da;font-size:.92rem}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primaryFormSubmit"]{background:linear-gradient(90deg,#2563eb,#06b6d4);border:0;color:#fff;font-weight:600}
.stTabs [data-baseweb="tab"]{padding:.5rem .7rem}
</style>
""", unsafe_allow_html=True)

st.markdown("""<style>
.act{display:inline-block;margin:.3rem .4rem .3rem 0;padding:.6rem 1rem;border-radius:12px;background:#2563eb;color:#fff!important;text-decoration:none!important;font-weight:600;font-size:.95rem}
.act.red{background:#dc2626}.act.green{background:#16a34a}
@media(max-width:640px){.hero h1{font-size:1.5rem}.res{justify-content:center;text-align:center}.block-container{padding-left:.8rem;padding-right:.8rem}}
</style>""", unsafe_allow_html=True)
_c1, _c2 = st.columns(2)
BIG = _c1.toggle("🔠 Large text / बड़े अक्षर", key="big_text")
HI = _c2.toggle("🇮🇳 हिन्दी निर्देश", key="hi_ui")
if BIG:
    st.markdown("<style>html{font-size:21px}.sub,.tbox,.sig,.stopbox,.safe,.disclaimer{font-size:1.1rem!important}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="hero"><h1>🛡️ Kavach AI</h1>'
    '<p><b>Anti-Digital-Arrest &amp; Scam Conversation Shield</b></p>'
    '<div class="chips"><span class="chip">Hindi</span><span class="chip">Hinglish</span><span class="chip">English</span>'
    '<span class="chip">Text</span><span class="chip">Audio</span><span class="chip">Voice recording</span></div></div>',
    unsafe_allow_html=True)
st.markdown(
    '<div class="disclaimer">Awareness prototype. The score counts known scam-pressure signals; it is <b>not</b> a probability or proof. '
    'It can miss scams or flag normal speech, so never rely on it alone.</div>', unsafe_allow_html=True)

# Whisper labels Hinglish as Urdu in "auto" mode, so Hinglish/English (Roman text) is the default.
LANG = {
    "Hinglish / English (Roman text, recommended)": "en",
    "Hindi (Devanagari text)": "hi",
    "Auto (Hindi or English only)": None,
}

SAMPLES = {
    "👮 Digital arrest (Hinglish)": "Main Crime Branch se bol raha hoon. Aap abhi digitally arrest ho. Kisi ko phone mat lagana aur account balance verify karne ke liye paise transfer karo turant.",
    "🏦 Bank OTP": "Your bank account will be blocked today. Tell me your OTP immediately to keep it active.",
    "👨‍👦 Son in custody": "I'm SHO speaking. We have caught your son in a drug-related case. If you want to save him, transfer ₹5 lakh immediately.",
    "✅ Normal call": "Hello, I am calling to confirm your appointment tomorrow at 5 pm. Please bring your reports.",
}

LEVEL_STYLE = {
    "Very high suspicion": ("#ef4444", "Strong scam pattern. Several classic pressure tactics are present together."),
    "High suspicion": ("#f97316", "Multiple scam signals found. Treat this as a likely scam until verified."),
    "Caution": ("#f59e0b", "Some warning signs found. Slow down and verify before doing anything."),
    "Lower detected signal": ("#22c55e", "Few or no known scam phrases found. This does not prove it is safe."),
}


def _highlight(text, phrases):
    safe = html.escape(text)
    if not phrases:
        return safe
    parts = []
    for ph in sorted(set(phrases), key=len, reverse=True):
        words = [re.escape(html.escape(w)) for w in ph.split()]
        if words:
            parts.append(r"\s+".join(words))
    if not parts:
        return safe
    try:
        return re.sub("(" + "|".join(parts) + ")", r"<mark>\1</mark>", safe, flags=re.IGNORECASE)
    except re.error:
        return safe


def build_report(text, result):
    lines = ["KAVACH AI - SCAM SIGNAL REPORT", datetime.now().strftime("%d %b %Y, %H:%M"),
             f"Score: {result['score']}/100 ({result['level']}). Heuristic only, not proof.", "", "Signals found:"]
    lines += [f"- {i['label']} (+{i['points']}): " + "; ".join(i["evidence"][:4]) for i in result["indicators"]] or ["- none"]
    lines += ["", "Conversation text:", text[-2500:], "", "What to do:"] + [f"- {r}" for r in result["recommendations"]]
    lines += ["", "Report: call 1930 or visit cybercrime.gov.in"]
    return "\n".join(lines)


def show_result(text, ctx="t"):
    result = analyze_conversation(text)
    score, level = result["score"], result["level"]
    if re.search(r"[\u0600-\u06FF]", text):
        st.warning("The transcript is in Urdu/Arabic script, which this detector cannot read. "
                   "Choose 'Hinglish / English (Roman text)' as the spoken language and record again, or correct the text.")
    color, subtitle = LEVEL_STYLE.get(level, LEVEL_STYLE["Lower detected signal"])

    st.markdown(
        f'<div class="res" style="--c:{color};--p:{score}"><div class="gauge"><div class="gin"><b>{score}</b><span>/100</span></div></div>'
        f'<div><div class="lvl">{html.escape(level)}</div><div class="sub">{html.escape(subtitle)}</div>'
        f'<div class="sub" style="font-size:.78rem;opacity:.8">{len(result["indicators"])} of {len(PATTERNS)} signal types detected · heuristic, not a probability</div></div></div>',
        unsafe_allow_html=True)

    if score >= 50:
        st.markdown(
            '<div class="stopbox">🛑 STOP. Do not transfer money, scan payment QR codes, or share OTP/PIN/passwords. '
            'Police and CBI never arrest anyone over a phone or video call. End the call and verify independently. '
            "If money is already sent, call <b>1930</b>."
            + ("<br>रुकिए! पैसे ट्रांसफर न करें और OTP/PIN किसी को न बताएं। पुलिस या CBI फोन/वीडियो कॉल पर गिरफ्तार नहीं करती। कॉल काटें और 1930 पर संपर्क करें।" if HI else "")
            + "</div>", unsafe_allow_html=True)

    if score >= 25:
        labels = ", ".join(i["label"] for i in result["indicators"])
        wa = "https://wa.me/?text=" + quote(f"Kavach AI alert: I may be getting a scam call (risk {score}/100: {labels}). Please call me. I will not send any money or OTP.")
        st.markdown(
            f'<a class="act red" href="tel:1930">📞 {"1930 पर कॉल करें" if HI else "Call 1930"}</a>'
            f'<a class="act green" href="{wa}" target="_blank" rel="noopener">💬 {"परिवार को बताएं" if HI else "Alert a family member"}</a>'
            '<a class="act" href="https://cybercrime.gov.in" target="_blank" rel="noopener">🌐 cybercrime.gov.in</a>', unsafe_allow_html=True)

    st.markdown('<div class="sec">🔎 Detected signals</div>', unsafe_allow_html=True)
    if result["indicators"]:
        for item in result["indicators"]:
            chips = "".join(f"<span>“{html.escape(e)}”</span>" for e in item["evidence"][:4])
            st.markdown(
                f'<div class="sig"><div class="sig-h"><span>{html.escape(item["label"])}</span>'
                f'<span class="pts">+{item["points"]}</span></div><div class="ev">{chips}</div></div>',
                unsafe_allow_html=True)
    else:
        st.markdown('<div class="safe">No configured scam phrase matched. This does not prove the conversation is safe.</div>', unsafe_allow_html=True)

    phrases = [e for item in result["indicators"] for e in item["evidence"]]
    st.markdown('<div class="sec">📄 Analyzed text</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="tbox">{_highlight(text[-2500:], phrases)}</div>', unsafe_allow_html=True)

    with st.expander("✅ What to do now", expanded=score >= 25):
        for item in result["recommendations"]:
            st.markdown(f"- {item}")
    st.download_button("⬇️ Download report (.txt)", build_report(text, result), file_name="kavach_report.txt", key=f"dl_{ctx}")


def run_transcribe(data, name, code):
    try:
        from transcriber import transcribe_audio
        with st.spinner("Transcribing… the first run downloads the speech model and can take a few minutes"):
            return transcribe_audio(data, name, code)
    except Exception as exc:
        st.error(f"Transcription failed: {type(exc).__name__}: {exc}")
        st.caption("Check internet on first run, package installation, and available RAM/disk space.")
        return None


def load_sample(sample_text):
    st.session_state["text_input"] = sample_text
    st.session_state["analyzed_text"] = sample_text


def clear_text():
    st.session_state["text_input"] = ""
    st.session_state["analyzed_text"] = ""


tab_text, tab_audio, tab_mic, tab_link, tab_learn = st.tabs(["📝 संदेश" if HI else "📝 Text", "🎙️ Upload", "⏺️ Record", "🔗 Link", "📚 Learn"])

# ---------------- Text ----------------
with tab_text:
    st.write("Paste English, Hindi (देवनागरी) or Roman Hinglish, or try a ready-made example:")
    cols = st.columns(2)
    for i, (label, sample) in enumerate(SAMPLES.items()):
        cols[i % 2].button(label, key=f"sample_{i}", on_click=load_sample, args=(sample,), use_container_width=True)

    with st.form("text_form", clear_on_submit=False):
        st.text_area("Conversation text", key="text_input", height=150,
                     placeholder="Yahan conversation paste/type karo…")
        c1, c2 = st.columns([3, 1])
        submitted = c1.form_submit_button("🔍 Analyze conversation", type="primary", use_container_width=True)
        c2.form_submit_button("Clear", on_click=clear_text, use_container_width=True)
    if submitted:
        st.session_state["analyzed_text"] = st.session_state.get("text_input", "").strip()
        if not st.session_state["analyzed_text"]:
            st.warning("Please enter some text first.")
    if st.session_state.get("analyzed_text"):
        show_result(st.session_state["analyzed_text"], "text")

# ---------------- Upload audio ----------------
with tab_audio:
    st.write("Upload a recording you have permission to analyze. For Hinglish keep the default (Roman text); choose Hindi for pure Hindi speech.")
    audio = st.file_uploader("Choose audio", type=["wav", "mp3", "m4a", "ogg", "flac", "webm"])
    language = st.selectbox("Spoken language", list(LANG), key="lang_upload")
    if audio:
        st.audio(audio)
        file_id = f"{audio.name}:{audio.size}"
        if st.session_state.get("upload_src") != file_id:  # new file -> drop the old transcript
            st.session_state.pop("upload_text", None)
            st.session_state["upload_src"] = file_id
        if st.button("🎙️ Transcribe & analyze", type="primary", key="transcribe_upload", use_container_width=True):
            transcript = run_transcribe(audio.getvalue(), audio.name, LANG[language])
            if transcript is not None:
                st.session_state["upload_text"] = transcript
                if not transcript.strip():
                    st.info("No speech was recognized. Try the Hindi option, clearer audio, or a larger model.")
    else:
        st.session_state.pop("upload_text", None)
        st.session_state.pop("upload_src", None)
    if audio and st.session_state.get("upload_text") is not None:
        edited = st.text_area("Transcript (you can correct it)", key="upload_text", height=130)
        if edited.strip():
            show_result(edited, "upload")

# ---------------- Record mic ----------------
with tab_mic:
    st.write("Record a short clip, then transcribe and analyze it. Mic access needs localhost or HTTPS.")
    mic_lang = st.selectbox("Spoken language", list(LANG), key="lang_mic")
    mic = st.audio_input("Record a clip")
    mic_id = hashlib.md5(mic.getvalue()).hexdigest() if mic else None
    if st.session_state.get("mic_src") != mic_id:  # new or removed recording -> drop the old transcript
        st.session_state.pop("mic_text", None)
        st.session_state["mic_src"] = mic_id
    if mic and st.button("🎙️ Transcribe & analyze recording", type="primary", key="transcribe_mic", use_container_width=True):
        transcript = run_transcribe(mic.getvalue(), "recording.wav", LANG[mic_lang])
        if transcript is not None:
            st.session_state["mic_text"] = transcript
            if not transcript.strip():
                st.info("No speech recognized. Try recording closer to the microphone.")
    if mic and st.session_state.get("mic_text") is not None:
        edited = st.text_area("Transcript (you can correct it)", key="mic_text", height=130)
        if edited.strip():
            show_result(edited, "mic")

# ---------------- Link checker ----------------
with tab_link:
    st.write("Paste a suspicious SMS/WhatsApp message or link. The check only reads the address text; the link is never opened.")
    link_in = st.text_area("Message or link", key="link_input", height=110, placeholder="https://sbi-kyc-update.xyz/login")
    if st.button("🔗 Check link", type="primary", key="check_link", use_container_width=True):
        st.session_state["link_checked"] = link_in
    if st.session_state.get("link_checked") is not None:
        found = find_links(st.session_state["link_checked"])
        if not found:
            st.info("No link found. Paste the full message or a web address.")
        for url in found[:10]:
            r = check_url(url)
            col = "#ef4444" if r["score"] >= 60 else "#f59e0b" if r["score"] >= 30 else "#22c55e"
            why = "".join(f"<span>{html.escape(x)}</span>" for x in r["reasons"])
            st.markdown(
                f'<div class="sig" style="border-color:{col}"><div class="sig-h"><span>{html.escape(r["host"] or r["url"])}</span>'
                f'<span class="pts" style="color:{col}">{html.escape(r["level"])} · {r["score"]}</span></div><div class="ev">{why}</div></div>',
                unsafe_allow_html=True)
        st.caption("A clean result does not prove a link is safe. Open banking links only by typing the official address yourself.")

# ---------------- Learn ----------------
LEARN = [
    ("👮 Digital arrest", "Caller claims to be police/CBI/customs and says you are 'under digital arrest'. No agency arrests anyone over a call. Hang up and call 1930."),
    ("🏦 KYC / account-block", "A message says your account or SIM will be blocked unless you update KYC or share an OTP. Banks never ask for OTP/PIN. Visit the branch or the official app."),
    ("📦 Parcel with drugs", "A courier 'finds' illegal items in a parcel in your name and connects you to a fake officer. Ignore it and do not stay on the video call."),
    ("📈 Investment / task jobs", "Groups promise daily profit or pay for simple online tasks, then ask for bigger deposits. Guaranteed returns are always a red flag."),
    ("🎁 Lottery / refund / QR", "You are told to scan a QR or accept a collect request to 'receive' money. Scanning only ever sends money out."),
    ("👨‍👦 Relative in trouble", "A voice says your son/daughter is in custody or hospital and needs money now. Call the relative directly on their own number first."),
]
with tab_learn:
    st.write("Common scams in India and what to do. Tap to read." if not HI else "भारत के आम स्कैम और बचाव। पढ़ने के लिए टैप करें।")
    for title, body in LEARN:
        with st.expander(title):
            st.write(body)
    st.info("Golden rule: no real officer, bank or company will ask you to stay on a call, keep it secret, pay money or share an OTP. Stop, hang up, verify, then call 1930 if you lost money.")

st.divider()
try:
    from transcriber import MODEL_SIZE
    model_note = f"Speech model: {MODEL_SIZE}. "
except Exception:
    model_note = ""
st.caption(
    model_note + "Privacy: analyze only conversations you are authorized to analyze. The app cannot tap phone-call audio. In India, for financial loss call your bank and 1930, or visit cybercrime.gov.in.")