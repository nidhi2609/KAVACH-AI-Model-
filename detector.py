"""Explainable multilingual (English / Hinglish / Hindi) scam-signal detector.

Rule based, NOT a trained ML model. Five signal groups add fixed points (max 100).
Patterns are written to be flexible (word gaps, spelling variants) so that real,
imperfect speech-to-text output is still caught.
"""
import re
import unicodedata

VERSION = "2.0"

_FAMILY = r"(?:son|daughter|child|kid|husband|wife|brother|sister|father|mother|papa|beta|beti|bete|relative)"
_ORG = (r"(?:police|cbi|c\.b\.i|ncb|narcotics|customs|cyber ?crime|cyber cell|crime branch|"
        r"enforcement directorate|income tax|trai|rbi|supreme court|high court|court|fedex|dhl|"
        r"mumbai police|delhi police|crime|dgi|sho|dsp|dcp|acp|ips|inspector|commissioner)")

# ---- building blocks for OTP / credential requests (Roman, Devanagari, mixed) ----
_OTP = r"(?<![a-z])(?:otp|o\.?\s?t\.?\s?p\.?|one[- ]time[- ]password)(?![a-z])|ओटीपी|ओटिपी|ओ\s?टी\s?पी|वन टाइम पासवर्ड"
_CRED = (r"(?:" + _OTP + r"|(?<![a-z])(?:upi pin|mpin|atm pin|pin(?!\s?code)|cvv|password|passcode|card number|card details|debit card|credit card|atm card|"
         r"aadhaar number|aadhar number|net banking|internet banking|bank details|account number|account details|login details)(?![a-z])"
         r"|पिन|पासवर्ड|सीवीवी|कार्ड नंबर|आधार नंबर)")
_VERB_LAT_ASK = r"(?<![a-z])(?:bhejo|bhej do|bhej|bhejiye|batao|bata do|bata|bataiye|batayein|batana|bolo|bol do|bol|de do|dedo|dijiye|dena|share|send|give|tell|provide|read out|read|forward|confirm|verify)(?![a-z])"
_VERB_DEV_ASK = r"भेजो|भेज दो|भेज|भेजिए|बताओ|बता दो|बताइए|बताएं|बोलो|दीजिए|दे दो|शेयर|सेंड|बता|बोल|कहो|बताना"
_VERB_ASK = r"(?:" + _VERB_LAT_ASK + r"|" + _VERB_DEV_ASK + r")"
_VERB_ANY = r"(?:" + _VERB_LAT_ASK + r"|(?<![a-z])(?:do|karo|kijiye)(?![a-z])|" + _VERB_DEV_ASK + r"|दो|करो|कीजिए)"
_GAP = r"(?:(?!(?<![a-z])(?:mat|not|never|nahi|nahin)(?![a-z])|मत|नहीं)[^.,;!?]){0,25}"

PATTERNS = [
 {"key": "fake_authority", "label": "Possible authority impersonation", "points": 15, "patterns": [
  # English
  r"\b(?:i am|i'm|this is|my name is|speaking)\b[^.!?]{0,45}\b(?:inspector|sho|dsp|dgi|dcp|acp|ips|officer|commissioner|cbi|ncb|customs|crime branch|cyber ?crime|cyber cell|narcotics|enforcement directorate)\b",
  r"\b(?:sho|dsp|dgi|dcp|acp|ips|inspector)\s+(?:\w+\s+){0,2}(?:speaking|here)\b",
  r"\b(?:calling|speaking|call(?:ing)?)\s+from\s+(?:the\s+)?(?:\w+\s+){0,2}" + _ORG + r"\b",
  r"\bthis is (?:the )?(?:cbi|police|customs|cyber ?crime|ncb|crime branch)\b",
  r"\bdigital(?:ly)? arrest\w*", r"\bmoney laundering\b",
  r"\bcrime branch\b", r"\bcyber ?crime (?:investigation )?(?:cell|department|branch|police|officer|official)\b", r"\bthis is (?:the )?(?:fedex|dhl|blue ?dart|india post|courier)\b", r"\bcyber cell\b",
  r"\bcentral bureau of investigation\b", r"\bnarcotics control bureau\b", r"\benforcement directorate\b",
  r"\b(?:cbi|ncb|ed|customs|police|trai|rbi) (?:officer|official|department|headquarters?|office)\b",
  r"\bsenior inspector\b", r"\b(?:police|cbi) (?:headquarters?|hq)\b",
  # Hinglish
  r"\b(?:main|mai|mein|hum)\b[^.!?]{0,40}\b(?:cbi|police|cyber ?crime|cyber cell|crime branch|customs|narcotics|ncb|dgi|sho|inspector)\b[^.!?]{0,25}\b(?:se|ka|ki|hoon|hu|hun|bol|baat)\b",
  r"\b(?:cbi|police|cyber cell|crime branch|customs|narcotics)\s+(?:department|office|headquarter\w*|se)\b",
  r"police wale", r"cyber cell se", r"cbi se", r"customs se",
  # Devanagari (no \b: it is unreliable with combining marks)
  r"पुलिस (?:विभाग|अधिकारी|मुख्यालय)", r"सीबीआई", r"क्राइम ब्रांच", r"साइबर (?:क्राइम|सेल)", r"नारकोटिक्स",
  r"डिजिटल अरेस्ट", r"(?:सीबीआई|पुलिस|कस्टम|क्राइम ब्रांच|साइबर सेल) से (?:बोल|बात)", r"इंस्पेक्टर", r"एनसीबी", r"मनी लॉन्ड्रिंग"]},

 {"key": "threat", "label": "Arrest, legal or account-block threat", "points": 25, "patterns": [
  r"\byou(?:'ll| will| are going to| shall)? (?:be |get )?(?:arrested|jailed|prosecuted|detained|go to jail)\b",
  r"\b(?:we|i)(?: will| shall|'ll)? (?:arrest|detain|jail) you\b", r"\barrest you\b",
  r"\b(?:you|your)\b[^.!?]{0,40}\barrest\w*", r"\bunder arrest\b", r"\barrest warrant\b", r"\blegal (?:action|proceedings|case)\b",
  r"\b(?:non[- ]?bailable|bailable) (?:arrest )?warrant\b", r"\bwarrant\b[^.!?]{0,30}\b(?:issued|prepared|registered|against you|in your name|under your name)\b",
  r"\b(?:case|fir|complaint|warrant)\b[^.!?]{0,25}\b(?:has been|is|was|will be) (?:prepared|registered|filed|lodged|issued)\b",
  r"\b(?:fir|case) (?:registered|filed|lodged)\b", r"\baction (?:will|shall) be taken\b",
  r"\b(?:caught|arrested|detained|held|kidnapped|nabbed)\s+(?:your|ur|the)\s+" + _FAMILY + r"\b",
  r"\b" + _FAMILY + r"\b[^.!?]{0,25}\b(?:in custody|in police custody|met with an accident|had an accident|is in (?:trouble|hospital|lockup))\b",
  r"\bimmediate detention\b", r"\b(?:you are|you're|aap)\b[^.!?]{0,20}\b(?:suspects?|accused|involved|under investigation|main accused)\b",
  r"\b(?:you|your)\b[^.!?]{0,30}\bsuspect\b", r"\bgo to jail\b", r"\bif you want to save\b",
  r"\bdrugs?\b[^.!?]{0,40}\b(?:case|parcel|package|racket|smuggl\w*|found|seized|buyers?|dealers?|trafficking)\b",
  r"\b(?:parcel|courier|package|consignment)\b[^.!?]{0,60}\b(?:drugs?|illegal|contraband|narcotics|passports?|fake|mdma|seized|customs)\b",
  r"\b(?:aadhaar|aadhar|adhar|adhaar)\b[^.!?]{0,60}\b(?:linked|misused|involved|connected|used)\b",
  r"\billegal (?:activit\w+|transactions?|use)\b",
  r"\b(?:your )?(?:bank )?(?:account|sim(?: card)?|number|mobile number|aadhaar|card|passport|upi|kyc)\b[^.!?]{0,20}\b(?:will be|is being|has been|is going to be|gets?)\s+(?:blocked|suspended|frozen|disconnected|cancelled|canceled|deactivated|seized|closed|terminated)\b",
  r"\b(?:or else|otherwise|warna|nahi to|nahin to)\b[^.!?]{0,40}\b(?:arrest|jail|block|case|fir|action|giraftar|suspend|freeze|disconnect)\w*",
  # Hinglish
  r"\bgi+ra+f+t+a+r\w*", r"\bgirf+t+a+r\w*", r"\barrest (?:ho|kar|kiya|hoge|honge|hone)\w*", r"\bpakad (?:liya|liye|lenge|jaoge|jayenge)\w*",
  r"\bjail (?:bhej|jaoge|jana|hogi|me)\w*", r"\bcase (?:darj|register|ban)\w*", r"\bpolice tumhe\b", r"\bwarrant (?:nikla|jaari|jari)\w*",
  r"\b(?:beta|beti|bete|son|bhai|papa)\b[^.!?]{0,25}\b(?:pakda|pakad|giraftar|police)\w*",
  r"\b(?:aadhaar|aadhar|adhar|adhaar)\b[^.!?]{0,40}\b(?:link|use|misuse)\w*",
  # Devanagari
  r"गिरफ्तार", r"गिरफ्तारी", r"जेल (?:भेज|जाओ|होगी)", r"वारंट", r"केस दर्ज", r"अरेस्ट", r"arrest\s*(?:हो|कर|किया)", r"एफआईआर", r"अकाउंट (?:बंद|ब्लॉक)", r"सिम (?:बंद|ब्लॉक)", r"ड्रग्स"]},

 {"key": "isolation", "label": "Instruction to keep it secret / stay on the call", "points": 20, "patterns": [
  r"\b(?:do not|don't|dont|never|must not|should not|cannot|can't)\s+(?:tell|inform|share this with|speak (?:to|with)|talk (?:to|with)|contact|call|involve|discuss(?: this)? with)\s+(?:\w+\s+){0,2}(?:anyone|anybody|any one|family|friends?|relatives?|parents?|wife|husband|police|bank|lawyer|counsel|advocate|neighbou?rs?|colleagues?)\b",
  r"\bkeep (?:this|it|the matter|the call|the case)\b[^.!?]{0,15}\b(?:secret|confidential|private|to yourself)\b",
  r"\b(?:this is|case is|matter is)\s+(?:strictly\s+)?(?:confidential|secret)\b", r"\bstrictly confidential\b",
  r"\b(?:stay|remain|keep|be)\s+(?:on|at)\s+(?:this |the )?(?:\w+\s+)?(?:call|line|video|video call|skype|whatsapp)\b",
  r"\bdo not (?:disconnect|hang up|cut|end|leave|switch off|turn off)\b", r"\bdon't (?:disconnect|hang up|cut the call|end the call|leave|switch off)\b",
  r"\b(?:turn on|keep|switch on|start) (?:your )?(?:video|camera)\b", r"\b(?:you )?(?:cannot|can't|must not) leave\b[^.!?]{0,20}\b(?:room|house|home|camera|frame)\b",
  # Hinglish
  r"\bkisi\s*(?:ko|se)\s+(?:bhi\s+)?(?:mat|na|nahi|nahin)\s+(?:bata|batan|bol|baat|kah|contact|call|phone)\w*",
  r"\bphone mat (?:laga|kar|kat)\w*", r"\bkisi ko phone mat\w*", r"\bkisi ko nahi batana\b", r"\b(?:ghar|family|parivar|papa|mummy|dost)\w*\s+(?:walon|walo|wale|ko|se)?\s*(?:ko\s+)?(?:mat|na|nahi)\s+(?:bata|bol|baat)\w*",
  r"\bcall mat (?:kat|cut|disconnect|band)\w*", r"\bphone mat (?:kat|band|rakh)\w*", r"\bline (?:par|pe) (?:bane|bana|rahe|raho|rehna)\w*", r"\bphone band mat\w*", r"\bvideo call (?:par|pe) (?:raho|bane|rehna)\w*",
  r"\bgopniy\w*", r"\bsecret rakho\b", r"\bkisi ko (?:bhi )?mat bata\w*",
  # Devanagari
  r"परिवार को मत बता\w*", r"किसी को (?:भी )?(?:मत|न|नहीं) बता\w*", r"किसी से (?:बात|संपर्क) (?:मत|न)", r"कॉल मत (?:काट|कट)\w*", r"फोन मत (?:लगा|काट|कर)\w*", r"वीडियो कॉल पर (?:बने रहो|रहो|रहना)", r"लाइन पर बने रह\w*", r"गोपनीय"]},

 {"key": "urgency", "label": "Urgency or pressure tactic", "points": 15, "patterns": [
  r"\bimmediately\b", r"\bright now\b", r"\bright away\b", r"\bact now\b", r"\bat once\b", r"\bwithout delay\b", r"\basap\b",
  r"\bwithin (?:the next )?(?:\d+|one|two|three|five|ten|half an?) (?:minutes?|mins?|hours?|hrs?)\b", r"\bonly \d+ (?:minutes?|mins?|hours?)\b",
  r"\b(?:last|final) (?:warning|chance|notice|opportunity)\b", r"\bbefore it(?:'s| is) too late\b", r"\btime is running out\b", r"\bdo it now\b", r"\burgent(?:ly)?\b",
  r"\b(?:transfer|send|pay|deposit|share|tell|give|verify|make)\b[^.,;!?]{0,60}\bnow\b",
  # Hinglish (plain "abhi" alone is too common; require an action word after it)
  r"\babhi\s+(?:\w+\s+){0,3}(?:karo|kar do|kijiye|bhejo|bhej do|transfer|batao|bataiye|do|de do|dena|jama|pay|share|verify|aao|bolo)\b",
  r"\babhi\s+abhi\b", r"\babhi ke abhi\b", r"\bturant\b", r"\btatkal\b", r"\bjaldi\s+(?:karo|se|bhejo|kijiye|kar)\w*", r"\bfatafat\b", r"\bder mat\b",
  r"\bisi (?:waqt|samay|minute|time)\b", r"\bforan\b", r"\bwarna\b", r"\b\d+ (?:minute|ghante|ghanta|min) (?:me|mein|ke andar)\b",
  # Devanagari
  r"तुरंत", r"तत्काल", r"फौरन", r"जल्दी (?:करो|से|भेजो|करें)", r"अभी के अभी", r"अभी\s+(?:\S+\s+){0,3}(?:करो|करें|भेजो|दो|बताओ|ट्रांसफर|जमा|भेज)", r"इसी (?:वक्त|समय)", r"वरना"]},

 {"key": "money_demand", "label": "Suspicious money-transfer demand", "points": 25, "negatable": True, "patterns": [
  r"\b(?:transfer|send|deposit|pay|wire|remit)\b[^.,;!?]{0,50}\b(?:₹|rs\.?|inr|rupees?|lakhs?|lacs?|thousand|crores?|\d{3,})",
  r"\btransfer (?:the |your |all )?(?:money|funds?|amount|balance|savings|account balance)\b", r"\b(?:transfer|send|move)\b[^.,;!?]{0,25}\b(?:account balance|savings|your balance)\b",
  r"\bsend (?:the |me |us )?(?:money|funds?|cash|amount|it)\b[^.,;!?]{0,30}\b(?:to|in|into)\b",
  r"\b(?:send|transfer|deposit|put)\b[^.,;!?]{0,30}\b(?:in|into|to)\s+(?:my|our|this|the|that|a)\s+(?:\w+\s+)?(?:account|upi|wallet)\b",
  r"\b(?:safe|secure|verification|rbi|government|clearance|escrow|holding|special|temporary) (?:account|vault|wallet)\b", r"\bgovernment (?:clearance )?vault\b",
  r"\b(?:make|do|complete)\s+(?:a |the )?(?:payment|deposit|transfer)\b", r"\b(?:payment|deposit|amount|fee|fine|penalty|deposit money)\b[^.,;!?]{0,25}\b(?:for|to avoid|to get|to clear)\b[^.,;!?]{0,20}\b(?:your )?(?:security|safety|verification|bail|release|clearance|case|arrest|detention|unblock|kyc|refund)\b",
  r"\bpay (?:a |the )?(?:fine|fee|penalty|bail|settlement|charges?|tax|deposit)\b", r"\b(?:bail|settlement|clearance|release) (?:amount|money|fee)\b",
  r"\b(?:gift cards?|bitcoin|crypto|usdt|google play card)\b[^.,;!?]{0,30}\b(?:buy|send|pay|purchase|transfer)\b",
  r"\b(?:scan|pay via|pay using)\b[^.,;!?]{0,15}\b(?:qr|upi|gpay|google pay|phonepe|paytm)\b", r"\bcollect request\b",
  # Hinglish
  r"\bpaise?\s+(?:transfer|bhej|bhejo|jama|deposit|de|do|dena|dene|send|pay)\w*", r"\bpaisa\s+(?:bhej|transfer|jama|de|do|dena|send)\w*",
  r"\b(?:amount|rakam|payment|raashi|rupaye|rupay|rupees?)\s+(?:transfer|bhej|bhejo|jama|deposit|karo|kar do|pay|dena)\w*", r"\bpayment\s+(?:karo|kar do|kijiye|karna|karni)\w*",
  r"\baccount (?:me|mein|main|par|pe)\s+(?:\w+\s+){0,2}(?:paise|paisa|amount|rupaye|transfer|jama)\w*", r"\b(?:account|balance)\s+(?:balance\s+)?(?:verify|transfer)\w*", r"\bbalance (?:transfer|verify|bhej)\w*",
  r"\bsurakshit account\b", r"\bsafe account (?:me|mein|main)\b",
  r"\baccount\s+(?:me|mai|mei|mein|main|has|have|contains?)\s+(?:\w+\s+){0,2}\d[\d,]*\s*(?:lakhs?|lacs?|crores?|thousand)\b", r"\bqr code scan karo\b", r"\bcollect request accept\b", r"\b(?:lottery|lucky draw|kbc|you(?:'ve| have) won|prize money)\b",
  # Devanagari
  r"पैसे (?:ट्रांसफर|भेज|जमा|दे)\w*", r"पैसा (?:भेज|ट्रांसफर|जमा)\w*", r"रुपये? (?:ट्रांसफर|भेज|जमा)\w*", r"(?:सेफ|सुरक्षित|वेरिफिकेशन) अकाउंट", r"ट्रांसफर करो", r"अकाउंट (?:में|मे) (?:पैसे|पैसा|रुपये)",
  r"(?:account|अकाउंट)\s+(?:में|मे|मैं)\s+(?:\S+\s+){0,2}(?:पैसे|पैसा|रुप(?:ये|ए)|ट्रांसफर|जमा)", r"(?:transfer|send|ट्रांसफर|सेंड)\s*(?:करो|कर दो|करें|करिए|कीजिए)", r"(?:ट्रांसफर|भेज|जमा)\w*[^.,;!?]{0,30}(?:लाख|हजार|करोड़|रुप(?:ये|ए))", r"(?:लाख|हजार|करोड़|रुप(?:ये|ए))[^.,;!?]{0,30}(?:ट्रांसफर|भेज|जमा)", r"पेमेंट (?:करो|करें)"]},
 {"key": "credential_request", "label": "Request for OTP / PIN / password / card or remote access", "points": 45, "negatable": True, "patterns": [
  # <credential> ... <ask verb>   and   <ask verb> ... <credential>  (works across Roman, Devanagari and mixed text)
  _CRED + _GAP + _VERB_ANY,
  _VERB_ASK + _GAP + _CRED,
  r"\bbank credentials\b", r"\b(?:otp|pin|cvv|password)\b[^.,;!?]{0,30}\b(?:immediately|now|right away|quickly|to keep|to verify)\b",
  r"\b(?:install|download|open)\b[^.,;!?]{0,20}\b(?:anydesk|teamviewer|quicksupport|screen ?share|remote)\w*", r"\bscreen ?shar\w*\b"]},
]
for group in PATTERNS:
    group["compiled"] = [re.compile(p, re.IGNORECASE) for p in group["patterns"]]

# "do not / never / mat" just before a match, or "mat" right after it, means a warning, not a demand.
NEGATION_BEFORE = re.compile(r"(?:do not|don't|dont|never|must not|should not|मत|mat)\s+([^\s,.;]+\s+){0,2}$", re.IGNORECASE)
NEGATION_AFTER = re.compile(r"^\s*(?:\w+\s+)?(?:mat|मत|nahi|nahin)\b", re.IGNORECASE)

RECOMMENDATIONS = [
 "Pause. Do not transfer money or share an OTP, password, PIN, or banking credential under pressure.",
 "End the call if you feel threatened. Real police/CBI never arrest anyone over a phone or video call.",
 "Verify claims independently using contact details from an official source, not details supplied by the caller.",
 "Talk to a trusted person or your bank before taking action.",
 "If money was transferred in India, call 1930 promptly and report at cybercrime.gov.in."
]

LEVELS = [
 (75, "Very high suspicion"),
 (50, "High suspicion"),
 (25, "Caution"),
 (0, "Lower detected signal"),
]


def normalize_text(text):
    text = unicodedata.normalize("NFC", text or "")
    text = text.lower().replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", text).strip()


def _negated(text, start, end):
    before = text[max(0, start - 35):start]
    return bool(NEGATION_BEFORE.search(before) or NEGATION_AFTER.search(text[end:end + 20]))


def level_for(score):
    for threshold, name in LEVELS:
        if score >= threshold:
            return name
    return LEVELS[-1][1]


def analyze_conversation(text):
    normalized = normalize_text(text)
    indicators, total = [], 0
    for group in PATTERNS:
        evidence = []
        for rx in group["compiled"]:
            for match in rx.finditer(normalized):
                if group.get("negatable") and _negated(normalized, match.start(), match.end()):
                    continue
                value = match.group(0).strip()
                if value and value not in evidence:
                    evidence.append(value)
        if evidence:
            total += group["points"]
            indicators.append({"key": group["key"], "label": group["label"], "points": group["points"], "evidence": evidence})
    score = min(total, 100)
    return {"score": score, "level": level_for(score), "indicators": indicators, "recommendations": RECOMMENDATIONS}