"""The scam-checking chatbot. Run with: python -m streamlit run streamlit_app.py

Where the pieces live:
    frontend/response_templates.py   the words on the screen
    frontend/intents.py              the questions the assistant can answer
    frontend/analyzer.py             the connection to the detector in backend/
    frontend/speech.py               read-aloud
"""

import streamlit as st

from frontend import intents, speech
from frontend import response_templates as rt
from frontend.analyzer import AnalysisError, analyze

# The language switch is drawn further down, but its value is needed from the first line.
LANGUAGE_LABELS = list(rt.LANGUAGES)
lang = rt.LANGUAGES[st.session_state.get("language_label", LANGUAGE_LABELS[0])]
ui = rt.UI[lang]

st.set_page_config(
    page_title=ui["page_title"],
    page_icon="🛡️",
    layout="centered",
)

# ---------------------------------------------------------------------------
# The only custom CSS: finger-sized buttons (N3). Everything else is themed in
# .streamlit/config.toml, which is the supported way to do it.
# ---------------------------------------------------------------------------
st.html(
    """
    <style>
      [class*="st-key-reply_"] button {
          min-height: 64px;
          font-weight: 600;
      }
    </style>
    """
)

# ---------------------------------------------------------------------------
# Session state: the whole conversation, and which step we are on.
# Assistant bubbles store what to say, not the words, so that switching language
# also translates the conversation so far.
# ---------------------------------------------------------------------------
if "chat" not in st.session_state:
    st.session_state["chat"] = [
        {
            "who": "assistant",
            "kind": "text",
            "ui": "greeting",
        }
    ]
    st.session_state["phase"] = "start"


def add(who, kind, **fields):
    """Append one bubble to the transcript."""
    st.session_state["chat"].append({"who": who, "kind": kind, **fields})


def bubble_text(entry):
    """The words of one text bubble in the current language."""
    if "ui" in entry:
        return ui[entry["ui"]]
    if "intent" in entry:
        return intents.reply(entry["intent"], lang)
    if "fallback" in entry:
        return intents.FALLBACK_REPLY[lang]
    if "replied" in entry:
        return (rt.AFTER_REPLIED if entry["replied"] else rt.AFTER_NOT_REPLIED)[lang]
    return entry["text"]


def draw_verdict(result, with_audio):
    """The verdict card, kept as short as it can be.

    On a phone every heading costs a third of a screen, so there are no
    subheadings here: the banner, the reasons, the steps and one call button.
    That is roughly 700px instead of the 1,300px the first version took.
    """
    level = str(result.get("risk_level", "medium")).lower()
    template = rt.template_for(level, lang)

    alert = {"high": st.error, "medium": st.warning, "low": st.success}.get(
        level, st.warning
    )
    alert(template["body"], title=f"{template['icon']} {template['headline']}")

    # Action before explanation. Someone who thinks they have been scammed
    # needs to know what to do in the next five minutes; why it was a scam is
    # interesting, useful for trusting the verdict, and entirely secondary.
    steps = "\n".join(
        f"**{number}.** {step}"
        for number, step in enumerate(template["steps"], start=1)
    )
    st.markdown(steps)

    st.link_button(
        ui["call_button"],
        "tel:18222",
        icon=":material/call:",
        width="stretch",
    )
    st.caption(ui["call_caption"])

    # One line, not three bullets. Requirement F3 still holds: the user can see
    # which signs fired, but it no longer costs them three lines of reading
    # before they reach the phone number.
    st.markdown(rt.why_line(result.get("matched_patterns"), lang))

    # Read-aloud, only on the newest verdict so old cards stay quiet in history.
    if with_audio:
        audio = speech.synthesize(speech.spoken_text(template), lang)
        if audio:
            st.audio(
                audio,
                format="audio/wav",
                autoplay=True,
                alt=ui["audio_alt"],
            )
            st.caption(ui["audio_replay"])
        else:
            st.caption(ui["audio_missing"])


def looks_like_question(text):
    """Cheap test used to decide between 'answer it' and 'check it'.

    A scam message almost never starts with "what" or ends with a question mark,
    so this one line keeps the two behaviours apart without any guessing.
    """
    lowered = text.strip().lower()
    starters = (
        "what", "why", "how", "who", "where", "when", "is ", "can ", "should", "do i", "does ",
        "甚麼", "什麼", "為甚麼", "為什麼", "點解", "點樣", "怎樣", "如何", "我應該", "應唔應該", "係咪", "是否",
    )
    return lowered.endswith(("?", "？")) or lowered.startswith(starters)


def check_message(text):
    """Run the detector and put the verdict in the transcript."""
    if len(text) > rt.MAX_MESSAGE_CHARS:
        add("assistant", "text", ui="too_long")
        return

    try:
        result = analyze(text)
    except AnalysisError:
        add("assistant", "text", ui="could_not_check")
        st.session_state["phase"] = "done"
        return

    # Very short text with nothing suspicious in it is probably not a message.
    # Chinese says the same thing in far fewer characters.
    shortest_message = 8 if intents.has_chinese(text) else 25
    if len(text) < shortest_message and not result.get("matched_patterns"):
        add("assistant", "text", ui="not_a_message")
        return

    add("assistant", "verdict", result=result)
    st.session_state["phase"] = "after"


def resolve(replied):
    """The user pressed Yes or No. Put their answer into the conversation."""
    add("user", "text", ui="answer_yes" if replied else "answer_no")
    add("assistant", "text", replied=replied)
    st.session_state["phase"] = "done"


# The question that changes the advice. It sits just above the chat box, not
# inside the transcript, because on a phone a button inside the transcript can
# slide underneath the pinned input box and become impossible to tap.


# ---------------------------------------------------------------------------
# Header. The big title only appears on the opening screen: once the
# conversation has started it is 300px of scrolling on a phone and tells the
# user something they already know.
# ---------------------------------------------------------------------------
st.radio("Language / 語言", LANGUAGE_LABELS, key="language_label", horizontal=True, label_visibility="collapsed")

if st.session_state["phase"] == "start":
    st.title(ui["title"])

st.markdown(rt.PRIVACY_NOTICE[lang])

# ---------------------------------------------------------------------------
# The conversation itself.
# ---------------------------------------------------------------------------
entries = st.session_state["chat"]
verdict_positions = [i for i, e in enumerate(entries) if e["kind"] == "verdict"]
newest_verdict = verdict_positions[-1] if verdict_positions else -1

for index, entry in enumerate(entries):
    avatar = "🛡️" if entry["who"] == "assistant" else "🙂"
    with st.chat_message(entry["who"], avatar=avatar):
        if entry["kind"] == "verdict":
            if index == newest_verdict:
                draw_verdict(entry["result"], with_audio=True)
            else:
                # An older check is folded down to one line. Keeping three full
                # cards in the transcript is what made the page scroll forever.
                old = rt.template_for(entry["result"].get("risk_level"), lang)
                st.markdown(f"{old['icon']} **{old['headline']}** {ui['checked_earlier']}")
        else:
            st.markdown(bubble_text(entry))

# The follow-up question, kept outside the transcript so it is always tappable.
if st.session_state["phase"] == "after":
    st.markdown(ui["follow_up_question"])
    no_column, yes_column = st.columns(2)
    if no_column.button(ui["answer_no"], key="reply_no", width="stretch"):
        resolve(replied=False)
        st.rerun()
    if yes_column.button(ui["answer_yes"], key="reply_yes", width="stretch"):
        resolve(replied=True)
        st.rerun()

# Example shortcuts, only before the first check.
# These are pills rather than buttons on purpose: a pills widget is one compact
# row by design, so there is no custom CSS involved and nothing to break on a
# small screen.
if st.session_state["phase"] == "start":
    st.caption(ui["examples_label"])
    choice = st.pills(
        "Try an example",
        [label for label, _ in rt.EXAMPLES[lang]],
        selection_mode="single",
        key=f"example_pick_{lang}",
        label_visibility="collapsed",
        width="content",
    )
    if choice and choice != st.session_state.get("example_done"):
        st.session_state["example_done"] = choice
        example_text = next(text for label, text in rt.EXAMPLES[lang] if label == choice)
        add("user", "text", text=example_text)
        check_message(example_text)
        st.rerun()

# ---------------------------------------------------------------------------
# Footer — two short lines instead of a paragraph (requirement T3).
# ---------------------------------------------------------------------------
st.caption(rt.FOOTER[lang])

# Room for the pinned chat box. Without this, the last line of text sits under
# the input on a phone and gets clipped mid-sentence.
st.space(180)

# ---------------------------------------------------------------------------
# The input. One box, used for both a pasted message and a question.
# ---------------------------------------------------------------------------
typed = st.chat_input(ui["input_placeholder"])
if typed:
    typed = typed.strip()
    if typed:
        add("user", "text", text=typed)
        intent = intents.match(typed)
        if intent:
            add("assistant", "text", intent=intent)
            if st.session_state["phase"] == "start":
                st.session_state["phase"] = "done"
        elif looks_like_question(typed):
            # A question we do not have an answer for. Say so, do not guess.
            add("assistant", "text", fallback=True)
            if st.session_state["phase"] == "start":
                st.session_state["phase"] = "done"
        else:
            check_message(typed)
        st.rerun()
