from detector import analyze_conversation


def keys(r):
    return {i["key"] for i in r["indicators"]}


# ---------- original tests ----------
def test_full_scam_sample():
    r = analyze_conversation("I am calling from the police department. Do not tell your family. Transfer the money to a safe account immediately or you will be arrested.")
    assert r["score"] == 100 and r["level"] == "Very high suspicion"


def test_guide_case_now_counts_as_urgency():
    r = analyze_conversation("Do not tell your family; transfer the money now or you will be arrested.")
    assert keys(r) == {"isolation", "money_demand", "urgency", "threat"} and r["score"] == 85


def test_normal_appointment():
    assert analyze_conversation("Hello, I am calling to confirm your appointment tomorrow.")["score"] == 0


def test_neutral_police_mention():
    assert analyze_conversation("The police station is near the market.")["score"] == 0


def test_bank_warning_not_flagged():
    r = analyze_conversation("Never share your OTP with anyone, says your bank.")
    assert "money_demand" not in keys(r) and "credential_request" not in keys(r)


def test_stay_on_call_is_isolation():
    assert "isolation" in keys(analyze_conversation("Stay on the video call and do not disconnect."))


def test_hinglish():
    r = analyze_conversation("Aap giraftar ho jaoge, kisi ko mat batao, abhi paise transfer karo")
    assert keys(r) == {"threat", "isolation", "urgency", "money_demand"}


def test_devanagari():
    r = analyze_conversation("आप गिरफ्तार हो जाएंगे, किसी को मत बताना, तुरंत पैसे ट्रांसफर करो")
    assert keys(r) == {"threat", "isolation", "urgency", "money_demand"}


def test_more_hinglish_variants():
    r = analyze_conversation("Main cyber cell se bol raha hu, family ko mat batana, abhi paise bhej do warna jail bhej denge")
    assert {"fake_authority", "isolation", "urgency", "money_demand", "threat"}.issubset(keys(r))


def test_empty_and_none():
    assert analyze_conversation("")["score"] == 0
    assert analyze_conversation(None)["score"] == 0


def test_score_capped_and_groups_counted_once():
    r = analyze_conversation("immediately immediately right now act now urgent")
    assert r["score"] == 15


def test_screenshot_digital_arrest_example():
    r = analyze_conversation("Main Crime Branch se bol raha hoon. Aap abhi digitally arrest ho. Kisi ko phone mat lagana aur account balance verify karne ke liye paise transfer karo turant.")
    assert r["score"] >= 70
    assert {"fake_authority", "threat", "isolation", "urgency", "money_demand"}.issubset(keys(r))


def test_screenshot_english_digital_arrest_example():
    r = analyze_conversation("This is Senior Inspector Verma from the Cyber Crime Investigation Cell. A non-bailable arrest warrant has been prepared. You must remain on this line, do not inform family members or local counsel, and transfer your account balance for verification.")
    assert r["score"] >= 75
    assert {"fake_authority", "threat", "isolation", "money_demand"}.issubset(keys(r))


def test_otp_blocked_account_example():
    r = analyze_conversation("Your bank account will be blocked today. Tell me your OTP immediately to keep it active.")
    assert r["score"] >= 50
    assert {"threat", "urgency", "credential_request"}.issubset(keys(r))


# ---------- new: real screenshots from the demo ----------
def test_mic_recording_garbled_speech():
    r = analyze_conversation("I am thief and I arrest you and to send in my account the lakh rupees.")
    assert r["score"] >= 50 and {"threat", "money_demand"}.issubset(keys(r))


def test_hinglish_crime_branch_transcript():
    r = analyze_conversation("Hello, main Crime Branch headquarter se baat kar raha hoon. Aapke number se illegal activities detect hui hain. Aap abhi digitally arrest ho. Kisi ko phone mat lagana aur account balance verify karne ke liye paise transfer karo turant.")
    assert r["score"] >= 90


def test_sho_son_drug_case():
    r = analyze_conversation("I'm SHO speaking. We have caught your son in a drug-related case. If you want to save him, transfer ₹5 lakh immediately")
    assert r["score"] >= 75
    assert {"fake_authority", "threat", "money_demand", "urgency"}.issubset(keys(r))


def test_dgi_suspect_drug_case():
    r = analyze_conversation("I am dgi suresh Am i talking to Mr sohan , you are our suspect for a drug case because your adhar is linked to a number which used to call drug buyers don't tell anyone and make a payment for your security")
    assert r["score"] >= 75
    assert {"fake_authority", "threat", "isolation", "money_demand"}.issubset(keys(r))


def test_parcel_scam():
    r = analyze_conversation("This is FedEx. A parcel in your name has been seized by customs with illegal drugs. Connect to the cyber crime officer on video call and do not disconnect.")
    assert r["score"] >= 50


# ---------- new: ordinary speech must stay low ----------
def test_abhi_alone_is_not_urgency():
    assert analyze_conversation("Abhi ghar aa raha hu, tum khana kha lena")["score"] == 0


def test_normal_hinglish_family_call():
    assert analyze_conversation("Mummy main office se nikal gaya hu, raat ko paneer banana")["score"] < 25


def test_news_style_sentence():
    assert analyze_conversation("The police arrested a thief near the market yesterday.")["score"] < 25


def test_hinglish_warning_not_flagged():
    r = analyze_conversation("Kabhi bhi OTP share mat karo, bank kabhi nahi maangta")
    assert "money_demand" not in keys(r)


def test_friend_payment_chat():
    assert analyze_conversation("I will pay you back tomorrow, thanks for lunch")["score"] < 25


# ---------- new: OTP requests in every transcript style Whisper can produce ----------
def test_otp_request_all_scripts():
    for s in ["Tumhare account mai 10 lakh rupee hai toh OTP bhejo",
              "तुम्हारे अकाउंट में 10 लाख रुपए है तो OTP भेजो",
              "account में 10 लाख रुपये हैं, ओटीपी भेजो",
              "Your account has 10 lakh rupees so send me the OTP",
              "O T P bhejo", "otp send karo", "ओ टी पी भेजो", "ओटीपी बताओ"]:
        r = analyze_conversation(s)
        assert "credential_request" in keys(r), s
        assert r["score"] >= 45, s


def test_otp_plus_money_lure_is_high():
    r = analyze_conversation("Tumhare account mai 10 lakh rupee hai toh OTP bhejo")
    assert r["score"] >= 70


def test_otp_warnings_not_flagged():
    for s in ["Kabhi bhi OTP share mat karo, bank kabhi nahi maangta", "OTP kisi ko mat batana",
              "Your OTP is 4821. Do not share it.", "What is your pin code of the area?"]:
        assert "credential_request" not in keys(analyze_conversation(s)), s