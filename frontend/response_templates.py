"""
The exact words the user sees on the Streamlit screen, in English ("en") and Traditional Chinese ("zh").

Together with intents.py, this is the only place to change the wording of the app.

Rules this file obeys (see docs/team/UX_GUIDELINES.md):
  - Plain words. No jargon. "fake message", never "phishing" / "social engineering".
  - Short sentences, one idea per line.
  - Calm tone, never alarmist, never blaming.
  - Every risk level ends with something to DO.
  - Never says "100% safe".
  - Never asks for personal information.
"""

# Label shown on the language switch -> language code. The first one is the default.
LANGUAGES = {"English": "en", "繁體中文": "zh"}

# Must be 2,000 characters or fewer, the limit agreed in docs/API_CONTRACT.md.
MAX_MESSAGE_CHARS = 2000

# ---------------------------------------------------------------------------
# 1. The reasons shown after "Why:"
# ---------------------------------------------------------------------------
# The keys are the pattern names sent by the backend (backend/patterns.py).
PATTERN_PLAIN = {
    "en": {
        "urgency": "it asks you to act fast",
        "money request": "it asks for money",
        "bank impersonation": "it pretends to be your bank",
        "government impersonation": "it pretends to be the police or government",
        "prize": "it says you have won something",
        "parcel": "it mentions a parcel",
        "job offer": "it offers a job you did not apply for",
        "investment": "it promises quick money",
        "romance": "it is from a stranger",
        "tech support": "it says your phone has a problem",
        "account problem": "it says your account will be blocked",
        "password request": "it asks for a password or code",
        "crypto": "it asks for cryptocurrency",
        "link": "it has a link",
        "personal details": "it asks for your personal details",
        "secrecy": "it tells you to keep it secret",
        "family impersonation": "it pretends to be family",
        "private chat": "it moves you to a private chat",
        "refund": "it offers a refund you did not expect",
        "automated call": "it is a recorded call",
        "known scam pattern": "it is like known scams",
        "unexpected charge": "it says you will be charged unless you call",
        "gambling": "it promotes online gambling",
        "phone number": "it asks you to call a number in the message",
    },
    "zh": {
        "urgency": "催促你盡快行動",
        "money request": "要求你付款",
        "bank impersonation": "假扮你的銀行",
        "government impersonation": "假扮警察或政府",
        "prize": "聲稱你中了獎",
        "parcel": "提及包裹",
        "job offer": "提供你沒有申請的工作",
        "investment": "承諾快速賺錢",
        "romance": "來自陌生人",
        "tech support": "聲稱你的電話有問題",
        "account problem": "聲稱你的戶口會被封鎖",
        "password request": "索取密碼或驗證碼",
        "crypto": "要求使用加密貨幣",
        "link": "含有連結",
        "personal details": "索取你的個人資料",
        "secrecy": "叫你保密",
        "family impersonation": "假扮你的親友",
        "private chat": "叫你轉到私人對話",
        "refund": "提供你意料之外的退款",
        "automated call": "是錄音來電",
        "known scam pattern": "與已知騙案相似",
        "unexpected charge": "聲稱會扣款，叫你致電取消",
        "gambling": "推廣網上賭博",
        "phone number": "叫你打訊息內的電話號碼",
    },
}

# Used if the backend sends a pattern that has no sentence above.
FALLBACK_REASON = {
    "en": "it uses wording scammers often use",
    "zh": "用了騙徒常用的字眼",
}

# The order the reasons are shown in. The most serious sign comes first.
PRIORITY = [
    "bank impersonation",
    "government impersonation",
    "password request",
    "family impersonation",
    "personal details",
    "money request",
    "secrecy",
    "unexpected charge",
    "phone number",
    "urgency",
    "prize",
    "investment",
    "gambling",
    "tech support",
    "account problem",
    "parcel",
    "job offer",
    "romance",
    "crypto",
    "refund",
    "private chat",
    "automated call",
    "known scam pattern",
    "link",
]

# ---------------------------------------------------------------------------
# 2. The three verdicts
# ---------------------------------------------------------------------------
# headline: the whole verdict in one sentence. body: two short sentences at most.
# steps: what to do next, in order, three at most.
TEMPLATES = {
    "en": {
        "high": {
            "icon": "🛑",
            "headline": "This looks like a scam.",
            "body": "Do not reply, and do not click anything in it. You did the right thing by checking.",
            "steps": [
                "Do not reply, and do not click any link.",
                "Do not send money, a password, or any code.",
                "Call your bank using the number on the back of your card.",
            ],
        },
        "medium": {
            "icon": "⚠️",
            "headline": "This message looks suspicious.",
            "body": "Some of the wording is used by scammers. It might still be real.",
            "steps": [
                "Do not send money or personal details yet.",
                "Do not use the link in the message.",
                "Ask someone you trust, or call your bank.",
            ],
        },
        "low": {
            "icon": "✅",
            "headline": "Nothing obviously dangerous here.",
            "body": "We did not find the usual signs of a scam. That is not a promise that it is safe.",
            "steps": [
                "Still be careful with messages from strangers.",
                "Never share your password, your PIN, or a code.",
                "If you feel unsure, ask a family member first.",
            ],
        },
    },
    "zh": {
        "high": {
            "icon": "🛑",
            "headline": "這看來是騙案。",
            "body": "請不要回覆，也不要點擊訊息內任何內容。你先查證是正確的做法。",
            "steps": [
                "不要回覆，也不要點擊任何連結。",
                "不要付款，也不要提供密碼或驗證碼。",
                "請撥打銀行卡背面的電話號碼，聯絡你的銀行。",
            ],
        },
        "medium": {
            "icon": "⚠️",
            "headline": "這個訊息有可疑。",
            "body": "當中部分字眼是騙徒常用的，但訊息也可能是真的。",
            "steps": [
                "暫時不要付款或提供個人資料。",
                "不要使用訊息內的連結。",
                "問問你信任的人，或致電你的銀行。",
            ],
        },
        "low": {
            "icon": "✅",
            "headline": "暫時沒有發現明顯危險。",
            "body": "我們找不到常見的騙案特徵，但這不代表一定安全。",
            "steps": [
                "收到陌生人的訊息，仍然要小心。",
                "絕不要透露密碼、PIN 或驗證碼。",
                "如果不放心，先問問家人。",
            ],
        },
    },
}

# If the backend sends something unexpected, behave as medium risk rather than as safe.
DEFAULT_LEVEL = "medium"

# ---------------------------------------------------------------------------
# 3. The replies to "have you already replied, or sent any money?"
# ---------------------------------------------------------------------------
AFTER_NOT_REPLIED = {
    "en": (
        "Good. Do not reply to it, and do not use any link or phone number inside it.\n\n"
        "If you want to be certain, call your bank on the number printed on the back "
        "of your card."
    ),
    "zh": (
        "很好。請不要回覆，也不要使用訊息內的連結或電話號碼。\n\n"
        "如果想確定，請撥打銀行卡背面的電話號碼，聯絡你的銀行。"
    ),
}

AFTER_REPLIED = {
    "en": (
        "**Please call your bank now.** Ask them to stop any payment, and tell them "
        "what you sent.\n\n"
        "1. Call the number on the back of your card.\n"
        "2. Keep the message. Do not delete it.\n"
        "3. Call 18222 to report it.\n\n"
        "This happens to many careful people. You did the right thing by checking."
    ),
    "zh": (
        "**請立即致電你的銀行。** 要求銀行停止任何付款，並告訴銀行你提供了甚麼。\n\n"
        "1. 撥打銀行卡背面的電話號碼。\n"
        "2. 保留訊息，不要刪除。\n"
        "3. 致電 18222 舉報。\n\n"
        "很多細心的人都遇過這種情況。你先查證是正確的做法。"
    ),
}

# ---------------------------------------------------------------------------
# 4. Everything else on the screen
# ---------------------------------------------------------------------------
PRIVACY_NOTICE = {
    "en": "**Your message is not saved.** We never ask for your name, password or bank details.",
    "zh": "**你的訊息不會被儲存。** 我們絕不會問你的姓名、密碼或銀行資料。",
}

FOOTER = {
    "en": "A guide, not a guarantee. If in doubt, call 18222.",
    "zh": "這只是指引，不是保證。如有疑問，請致電 18222。",
}

UI = {
    "en": {
        "page_title": "Scam check",
        "title": "Is this message a scam?",
        "greeting": "Hello. Paste the message you are worried about, or press an example.",
        "input_placeholder": "Paste the message here",
        "examples_label": "No message to hand? Try one:",
        "call_button": "Call 18222 — Anti-Scam Helpline",
        "call_caption": "Or call the number on the back of your bank card.",
        "why": "**Why:**",
        "why_none": "none of the usual scam signs are here.",
        "audio_replay": "Press play to hear it again.",
        "audio_missing": "Read-aloud is not available on this computer.",
        "audio_alt": "A spoken version of this warning",
        "checked_earlier": "_(checked earlier)_",
        "could_not_check": "I could not check that message right now. Please call the Anti-Scam Helpline on 18222.",
        "not_a_message": "I do not see a message there. Paste the message you received and I will check it.",
        "too_long": "That message is too long to check. Please copy the most important part.",
        "follow_up_question": "**Have you already replied to it, or sent any money?**",
        "answer_no": "No, I have not",
        "answer_yes": "Yes, I did",
    },
    "zh": {
        "page_title": "騙案檢查",
        "title": "這個訊息是騙案嗎？",
        "greeting": "你好。請貼上令你擔心的訊息，或按下面的例子。",
        "input_placeholder": "在這裏貼上訊息",
        "examples_label": "手上沒有訊息？試試這些：",
        "call_button": "致電 18222 — 防騙易熱線",
        "call_caption": "或撥打銀行卡背面的電話號碼。",
        "why": "**原因：**",
        "why_none": "沒有發現常見的騙案特徵。",
        "audio_replay": "按播放可再聽一次。",
        "audio_missing": "這部電腦未能讀出內容。",
        "audio_alt": "這個警告的語音版本",
        "checked_earlier": "_（早前檢查）_",
        "could_not_check": "我現在未能檢查這個訊息。請致電防騙易熱線 18222。",
        "not_a_message": "我看不到訊息內容。請貼上你收到的訊息，我會幫你檢查。",
        "too_long": "這個訊息太長，未能檢查。請複製最重要的部分。",
        "follow_up_question": "**你已經回覆了，或者付了款嗎？**",
        "answer_no": "沒有",
        "answer_yes": "有",
    },
}

# ---------------------------------------------------------------------------
# 5. The example buttons. Only use made-up addresses here.
# ---------------------------------------------------------------------------
EXAMPLES = {
    "en": [
        (
            "Bank",
            "HSBC ALERT: A payment of $2,300 to an unknown account was detected. "
            "Your account will be SUSPENDED unless you confirm your identity now: "
            "http://hsbc-verify-secure.top/login",
        ),
        (
            "Parcel",
            "Your parcel is on hold. Please update your delivery address at parcel-track.info",
        ),
        (
            "Family",
            "Hi Mum, I'll pick up the shopping on my way home. Do you need anything "
            "from the shop? See you at 6.",
        ),
    ],
    "zh": [
        (
            "銀行",
            "【滙豐】閣下戶口出現異常，已被凍結。請立即到以下網址核實身份並提供驗證碼："
            "http://hsbc-verify-secure.top/login",
        ),
        (
            "包裹",
            "你的包裹暫時滯留，請到 parcel-track.info 查看。",
        ),
        (
            "家人",
            "阿媽，我今晚買餸返嚟，你唔使煮飯，六點見。",
        ),
    ],
}


def _rank(pattern):
    key = str(pattern).strip().lower()
    return PRIORITY.index(key) if key in PRIORITY else len(PRIORITY)


def plain_reasons(matched_patterns, language="en", limit=3):
    """Turn backend pattern names into short phrases, most serious first. Never empty."""
    phrases = []
    for pattern in sorted(matched_patterns or [], key=_rank):
        key = str(pattern).strip().lower()
        phrase = PATTERN_PLAIN[language].get(key, FALLBACK_REASON[language])
        if phrase not in phrases:
            phrases.append(phrase)
        if len(phrases) >= limit:
            break
    return phrases or [FALLBACK_REASON[language]]


def why_line(matched_patterns, language="en"):
    """The single "Why:" line under the verdict."""
    text = UI[language]
    if not matched_patterns:
        return f"{text['why']} {text['why_none']}"
    reasons = plain_reasons(matched_patterns, language)
    if language == "zh":
        return f"{text['why']}{'、'.join(reasons)}。"
    # Only the first phrase keeps its "it", so the line reads as one sentence.
    tail = [reason.removeprefix("it ") for reason in reasons[1:]]
    return f"{text['why']} {', '.join([reasons[0], *tail])}."


def template_for(risk_level, language="en"):
    """Return the template dict for a risk level, defaulting safely."""
    key = str(risk_level).strip().lower()
    return TEMPLATES[language].get(key, TEMPLATES[language][DEFAULT_LEVEL])
