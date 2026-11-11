"""Runs streamlit_app.py in-process with Streamlit's AppTest, using the real detector."""

import os

from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "streamlit_app.py")

BANK = "HSBC ALERT: A payment of $2,300 was detected. Confirm your identity now: http://hsbc-verify.top"


def fresh():
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception, [e.value for e in app.exception]
    return app


def texts(app):
    """Everything the app is currently showing as text (any element type)."""
    parts = []
    for group in (app.markdown, app.subheader, app.caption, app.text, app.title):
        parts.extend(item.value for item in group)
    return " ".join(parts)


def press(app, key):
    for button in app.button:
        if button.key == key:
            button.click().run()
            return app
    raise AssertionError(f"no button with key {key}")


def pick_example(app, label):
    """Choose one of the example pills."""
    app.pills[0].set_value(label).run()
    return app


def say(app, message):
    app.chat_input[0].set_value(message).run()
    return app


def test_screen_one():
    app = fresh()
    assert app.title[0].value == "Is this message a scam?"
    assert len(app.chat_input) == 1, "there should be one chat box"
    assert "not saved" in texts(app), "privacy notice must be visible first"
    assert "Hello" in texts(app), "the assistant should greet the user"
    print("  OK  greeting, privacy notice, one chat box")


def test_empty_input_guard():
    app = fresh()
    say(app, "hi")
    assert "do not see a message there" in texts(app)
    print("  OK  short nonsense gets a helpful nudge, not a fake verdict")


def test_message_verdict():
    app = fresh()
    say(app, BANK)
    assert app.error, "a bank scam should produce the red verdict"
    body = texts(app)
    assert "pretends to be your bank" in body, "the reasons must be shown"
    assert "Do not reply, and do not click any link." in body, "the steps must be shown"
    assert "already replied" in body, "the follow-up question must appear"
    print("  OK  pasted message → verdict card → follow-up question")


def test_follow_up_no():
    app = fresh()
    say(app, BANK)
    press(app, "reply_no")
    assert "No, I have not" in texts(app), "the answer should appear in the conversation"
    assert "Do not reply to it" in texts(app)
    print("  OK  answering 'No' gives the calm reminder")


def test_follow_up_yes():
    app = fresh()
    say(app, BANK)
    press(app, "reply_yes")
    assert "Please call your bank now" in texts(app)
    assert "18222" in texts(app)
    print("  OK  answering 'Yes' gives the emergency script")


def test_obvious_scam_is_red():
    """The exact message that came out green in the first phone test."""
    app = fresh()
    say(app, "Your bank account is hacked give me money")
    assert app.error, "an obvious scam must never come out green"
    print("  OK  'bank account hacked give me money' is high risk")


def test_example_buttons():
    app = fresh()
    pick_example(app, "Bank")
    assert app.error, "the bank example should be high risk"
    print("  OK  example pill still works inside the chat")


def test_intents():
    app = fresh()
    say(app, BANK)
    app = say(app, "what is 18222")
    assert "Anti-Scam Helpline" in texts(app)
    app = say(app, "i clicked the link")
    assert "Close the page now" in texts(app)
    print("  OK  typed questions are answered from intents")


def test_unknown_question():
    app = fresh()
    say(app, BANK)
    say(app, "what is the weather in hong kong tomorrow")
    assert "not sure about that one" in texts(app)
    print("  OK  an unknown question gets an honest 'I do not know'")


def test_three_levels():
    app = fresh()
    pick_example(app, "Bank")
    assert len(app.error) == 1
    app = fresh()
    pick_example(app, "Parcel")
    assert len(app.warning) == 1
    app = fresh()
    pick_example(app, "Family")
    assert len(app.success) == 1
    print("  OK  the three examples still hit red, amber and green")


def test_voice_or_honesty():
    app = fresh()
    pick_example(app, "Bank")
    captions = " ".join(c.value for c in app.caption)
    assert ("Press play" in captions) or ("not available on this computer" in captions)
    print("  OK  read-aloud is offered, or the reason is stated plainly")


def test_too_long_message_gets_a_clear_reply():
    app = fresh()
    say(app, "a" * 2001)
    assert "too long to check" in texts(app)


def test_no_placeholder_label_remains():
    assert "placeholder" not in texts(fresh()).lower()


def switch_to_chinese(app):
    app.radio[0].set_value("繁體中文").run()
    assert not app.exception, [e.value for e in app.exception]
    return app


def test_english_is_the_default():
    app = fresh()
    assert app.radio[0].value == "English"
    assert "Is this message a scam?" in texts(app)


def test_switch_shows_chinese_and_translates_the_conversation():
    app = fresh()
    pick_example(app, "Bank")
    assert "do not click anything" in app.error[0].value
    press(app, "reply_no")
    assert "Do not reply to it" in texts(app)
    switch_to_chinese(app)
    body = texts(app)
    assert "請不要回覆，也不要使用訊息內的連結" in body
    assert "你的訊息不會被儲存" in body
    assert "Do not reply to it" not in body


def test_switching_back_restores_english():
    app = switch_to_chinese(fresh())
    app.radio[0].set_value("English").run()
    assert "Is this message a scam?" in texts(app)


def test_chinese_examples_hit_all_three_levels():
    app = switch_to_chinese(fresh())
    app.pills[0].set_value("銀行").run()
    assert len(app.error) == 1
    assert "假扮你的銀行" in texts(app)
    app = switch_to_chinese(fresh())
    app.pills[0].set_value("包裹").run()
    assert len(app.warning) == 1
    app = switch_to_chinese(fresh())
    app.pills[0].set_value("家人").run()
    assert len(app.success) == 1


def test_chinese_question_gets_a_chinese_answer():
    app = switch_to_chinese(fresh())
    say(app, "18222是什麼")
    assert "防騙易熱線" in texts(app)


def test_chinese_unknown_question_is_honest():
    app = switch_to_chinese(fresh())
    say(app, "明天天氣如何？")
    assert "這個問題我不肯定" in texts(app)


def test_short_chinese_message_is_still_checked():
    app = switch_to_chinese(fresh())
    say(app, "阿媽今晚我唔返嚟食飯")
    assert len(app.success) == 1


def test_english_message_gets_chinese_wording_when_chinese_is_selected():
    app = switch_to_chinese(fresh())
    say(app, BANK)
    assert "也不要點擊訊息內任何內容" in app.error[0].value


def test_pasted_scam_containing_an_intent_phrase_is_still_checked():
    app = fresh()
    say(app, "Mum please help me, I lost my phone and this is my new number. Transfer HK$8,000 to my friend now.")
    assert app.error or app.warning
    assert "I can check a message" not in texts(app)
