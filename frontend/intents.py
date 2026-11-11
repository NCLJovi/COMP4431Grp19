"""The short list of questions the assistant can actually answer, in English and Traditional Chinese.

An elderly user asking "is my bank really calling?" needs a correct answer, not a fluent guess. Everything
outside these questions gets an honest "I am not sure, please call 18222" instead of an invented reply.

Matching is a plain "does the message contain this phrase" test. Phrases must be lowercase. The phrases of
both languages are always checked, and the reply follows the language chosen on the screen.
"""

INTENTS = [
    {
        "name": "call_the_number",
        "phrases": {
            "en": ["call the number", "should i call", "can i call", "phone them", "call them back", "ring them"],
            "zh": ["打那個號碼", "打個電話", "打返俾佢", "應該打電話", "可以打電話", "要不要回電", "應唔應該覆電"],
        },
        "reply": {
            "en": (
                "Please do not use any phone number that was inside the message. "
                "Scammers put their own number there. "
                "Call your bank using the number printed on the back of your card, "
                "or call 18222."
            ),
            "zh": (
                "請不要使用訊息內的任何電話號碼，騙徒會放自己的號碼。"
                "請撥打銀行卡背面的電話號碼聯絡銀行，或致電 18222。"
            ),
        },
    },
    {
        "name": "is_bank_calling",
        "phrases": {
            "en": ["is my bank calling", "bank called me", "bank rang me", "really from my bank", "is it really my bank"],
            "zh": ["銀行打給我", "銀行打電話給我", "銀行打俾我", "銀行打嚟", "真的是銀行", "係咪銀行"],
        },
        "reply": {
            "en": (
                "Your bank will never ask for your password or a code by message or phone. "
                "If you are not sure, hang up and call the number on your card."
            ),
            "zh": (
                "銀行絕不會透過訊息或電話索取你的密碼或驗證碼。"
                "如果不肯定，請掛線，再撥打銀行卡上的電話號碼。"
            ),
        },
    },
    {
        "name": "clicked_link",
        "phrases": {
            "en": ["i clicked", "clicked the link", "opened the link", "opened the website", "i pressed the link"],
            "zh": ["我點擊了", "點擊了連結", "打開了連結", "打開了網站", "我按了連結", "撳咗", "開咗個網站"],
        },
        "reply": {
            "en": (
                "Do not worry — this happens to many people. "
                "Close the page now. Do not type anything into it. "
                "If you entered a password or a card number, call your bank straight away "
                "and tell them what happened."
            ),
            "zh": (
                "不用擔心，很多人都遇過這種情況。"
                "請立即關閉網頁，不要輸入任何內容。"
                "如果你已輸入密碼或信用卡號碼，請馬上致電銀行說明情況。"
            ),
        },
    },
    {
        "name": "sent_details",
        "phrases": {
            "en": [
                "i gave my password", "i entered my password", "i gave them my card", "i sent the money",
                "i transferred", "i paid", "i gave them the code", "i told them the code",
            ],
            "zh": [
                "我給了密碼", "輸入了密碼", "俾咗密碼", "給了驗證碼", "俾咗驗證碼", "我付了款", "我轉了帳",
                "我已經轉帳", "過咗數", "俾咗錢",
            ],
        },
        "reply": {
            "en": (
                "Please act now, and do not feel foolish — these messages are built to fool people. "
                "Call your bank immediately and ask them to stop any payment. "
                "Then call 18222 to report it. Keep the message so it can be shown to them."
            ),
            "zh": (
                "請立即行動，不用自責，這些訊息就是設計來欺騙人的。"
                "請馬上致電銀行，要求停止任何付款，然後致電 18222 舉報。請保留訊息，以便出示。"
            ),
        },
    },
    {
        "name": "what_is_18222",
        "phrases": {
            "en": ["what is 18222", "who is 18222", "anti-scam", "helpline", "report it", "where do i report"],
            "zh": ["什麼是18222", "甚麼是18222", "18222是", "18222 是", "18222係", "18222 係", "防騙易", "點樣報案", "如何報案", "去邊度報案"],
        },
        "reply": {
            "en": (
                "18222 is the Hong Kong Anti-Scam Helpline. It is free, and you can call it "
                "when you are not sure about a message. They will not ask for your password."
            ),
            "zh": (
                "18222 是香港的防騙易熱線，服務免費。"
                "如果對訊息有懷疑，可以致電查詢。他們不會問你的密碼。"
            ),
        },
    },
    {
        "name": "is_it_safe",
        "phrases": {
            "en": ["is it safe", "so it is safe", "can i trust", "is it real", "am i safe"],
            "zh": ["安全嗎", "安唔安全", "可以相信嗎", "是真的嗎", "係咪真", "信得過"],
        },
        "reply": {
            "en": (
                "I cannot promise that a message is safe — nobody can. "
                "I can only tell you what the usual signs look like. "
                "If anything still feels wrong, trust that feeling and call 18222."
            ),
            "zh": (
                "我不能保證訊息一定安全，沒有人可以。"
                "我只能告訴你常見的騙案特徵。如果仍然覺得不妥，請相信自己的感覺，致電 18222。"
            ),
        },
    },
    {
        "name": "what_can_you_do",
        "phrases": {
            "en": ["what can you do", "help me", "what do i do", "how does this work"],
            "zh": ["你可以做甚麼", "你可以做什麼", "你識做咩", "點樣用", "如何使用", "我應該怎麼辦", "我應該點做"],
        },
        "reply": {
            "en": (
                "I can check a message you received and tell you if it looks like a scam. "
                "Paste the message here and I will look at it. "
                "I can also tell you who to call."
            ),
            "zh": (
                "我可以檢查你收到的訊息，告訴你它是否像騙案。"
                "請在這裏貼上訊息，我會幫你看看，也可以告訴你應該聯絡誰。"
            ),
        },
    },
    {
        "name": "thanks",
        "phrases": {
            "en": ["thank you", "thanks", "ok thank", "bye"],
            "zh": ["謝謝", "多謝", "再見", "拜拜", "唔該晒"],
        },
        "reply": {
            "en": (
                "You are welcome. You did the right thing by checking. "
                "If another message worries you, come back any time."
            ),
            "zh": "不用客氣。你先查證是正確的做法。如果再收到令你擔心的訊息，歡迎隨時回來。",
        },
    },
]

# What the assistant says when it does not recognise the question.
FALLBACK_REPLY = {
    "en": (
        "I am not sure about that one, and I do not want to guess. "
        "You can paste the message here and I will check it. "
        "For anything else, call the Anti-Scam Helpline on 18222."
    ),
    "zh": (
        "這個問題我不肯定，也不想亂猜。"
        "你可以在這裏貼上訊息，我會幫你檢查。其他問題請致電防騙易熱線 18222。"
    ),
}

# A longer text is treated as a pasted message, even if it contains a phrase such as "help me".
MAX_QUESTION_CHARS = {"en": 60, "zh": 30}


def has_chinese(text):
    return any("一" <= character <= "鿿" for character in text)


def match(text):
    """Return the name of the matching intent, or None. First phrase that appears wins."""
    if len(text) > MAX_QUESTION_CHARS["zh" if has_chinese(text) else "en"]:
        return None
    lowered = text.lower()
    for intent in INTENTS:
        for phrases in intent["phrases"].values():
            if any(phrase in lowered for phrase in phrases):
                return intent["name"]
    return None


def reply(name, language="en"):
    """The reply for an intent name in the chosen language."""
    return next(intent["reply"][language] for intent in INTENTS if intent["name"] == name)
