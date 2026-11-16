"""The scam-checking chatbot. Run with: python -m streamlit run streamlit_app.py

Where the pieces live:
    frontend/response_templates.py   the words on the screen
    frontend/intents.py              greetings, booking requests and the questions it can answer
    backend/booking.py               the consultation booking demo
    frontend/analyzer.py             the connection to the detector in backend/
    frontend/speech.py               read-aloud
"""

from datetime import date

import streamlit as st

from backend import booking
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
      [class*="st-key-reply_"] button,
      [class*="st-key-menu_"] button,
      [class*="st-key-book_"] button {
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
    if "booking" in entry:
        return rt.booking_text(entry, lang)
    if "day" in entry:
        return rt.day_label(date.fromisoformat(entry["day"]), lang)
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


# ---------------------------------------------------------------------------
# Consultation booking: choose a day, choose a time, confirm.
# st.session_state["booking"] holds the day and time chosen so far.
# ---------------------------------------------------------------------------
def start_booking():
    st.session_state["booking"] = {}
    add("assistant", "text", booking="ask_day")
    st.session_state["phase"] = "book_day"


def choose_day(day):
    free = booking.free_times(day)
    if not free:
        add("assistant", "text", booking="day_full", date=day.isoformat())
        st.session_state["phase"] = "book_day"
        return
    st.session_state["booking"] = {"date": day.isoformat()}
    add("assistant", "text", booking="ask_time", date=day.isoformat(), free=free)
    st.session_state["phase"] = "book_time"


def choose_time(time):
    chosen = st.session_state["booking"]
    day = date.fromisoformat(chosen["date"])
    free = booking.free_times(day)
    if time in free:
        chosen["time"] = time
        add("assistant", "text", booking="confirm", date=chosen["date"], time=time)
        st.session_state["phase"] = "book_confirm"
    elif not free:
        choose_day(day)
    else:
        sentence = "taken" if time in booking.SLOT_TIMES else "not_a_slot"
        add("assistant", "text", booking=sentence, date=chosen["date"], time=time, free=free)
        st.session_state["phase"] = "book_time"


def confirm_booking(agreed):
    chosen = st.session_state["booking"]
    if not agreed:
        add("assistant", "text", booking="change")
        start_booking()
        return
    try:
        reference = booking.book(date.fromisoformat(chosen["date"]), chosen["time"])
    except booking.SlotTaken:
        # Someone else took the slot while this user was deciding.
        choose_time(chosen["time"])
        return
    add("assistant", "text", booking="booked", date=chosen["date"], time=chosen["time"], ref=reference)
    st.session_state["phase"] = "done"


def cancel_booking():
    add("assistant", "text", booking="cancelled")
    st.session_state["phase"] = "menu"


def booking_reply(text):
    """Handle a typed line during a booking. Returns False if the line was not about the booking."""
    phase = st.session_state["phase"]
    if intents.CANCEL.search(text):
        cancel_booking()
        return True
    if phase == "book_confirm":
        if intents.YES.match(text) or intents.NO.match(text):
            confirm_booking(bool(intents.YES.match(text)))
            return True
        return False
    day = booking.parse_day(text, booking.open_days())
    if day:
        choose_day(day)
    time = booking.parse_time(text, bare=phase == "book_time" and not day)
    if time and st.session_state["phase"] == "book_time":
        choose_time(time)
    return bool(day or (time and phase == "book_time"))


def booking_prompt():
    """Repeat the current booking question after a line that was not understood."""
    phase = st.session_state["phase"]
    chosen = st.session_state["booking"]
    if phase == "book_day":
        add("assistant", "text", booking="which_day")
    elif phase == "book_time":
        free = booking.free_times(date.fromisoformat(chosen["date"]))
        add("assistant", "text", booking="which_time", date=chosen["date"], free=free)
    else:
        add("assistant", "text", booking="yes_or_no", date=chosen["date"], time=chosen["time"])


# The buttons below sit just above the chat box, not inside the transcript,
# because on a phone a button inside the transcript can slide underneath the
# pinned input box and become impossible to tap.


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

# The two things the assistant can do, offered whenever nothing is in progress.
if st.session_state["phase"] in ("start", "menu", "done"):
    check_column, book_column = st.columns(2)
    if check_column.button(ui["menu_check"], key="menu_check", icon=":material/search:", width="stretch"):
        add("user", "text", ui="menu_check")
        add("assistant", "text", ui="ask_message")
        st.session_state["phase"] = "check"
        st.rerun()
    if book_column.button(ui["menu_book"], key="menu_book", icon=":material/event:", width="stretch"):
        add("user", "text", ui="menu_book")
        start_booking()
        st.rerun()

# Booking: the days, then the times. A slot that is taken is greyed out.
if st.session_state["phase"] == "book_day":
    with st.container(horizontal=True):
        for day in booking.open_days():
            full = not booking.free_times(day)
            label = rt.day_label(day, lang)
            label = ui["booking_full_label"].format(day=label) if full else label
            if st.button(label, key=f"day_{day.isoformat()}", disabled=full):
                add("user", "text", day=day.isoformat())
                choose_day(day)
                st.rerun()

if st.session_state["phase"] == "book_time":
    taken = booking.taken_times(date.fromisoformat(st.session_state["booking"]["date"]))
    with st.container(horizontal=True):
        for time in booking.SLOT_TIMES:
            label = ui["booking_taken_label"].format(time=time) if time in taken else time
            if st.button(label, key=f"time_{time.replace(':', '')}", disabled=time in taken):
                add("user", "text", text=time)
                choose_time(time)
                st.rerun()

if st.session_state["phase"] == "book_confirm":
    no_column, yes_column = st.columns(2)
    if no_column.button(ui["booking_no"], key="book_no", width="stretch"):
        add("user", "text", ui="booking_no")
        confirm_booking(False)
        st.rerun()
    if yes_column.button(ui["booking_yes"], key="book_yes", type="primary", width="stretch"):
        add("user", "text", ui="booking_yes")
        confirm_booking(True)
        st.rerun()

if st.session_state["phase"].startswith("book_"):
    if st.button(ui["booking_cancel"], key="cancel_booking", type="tertiary"):
        add("user", "text", ui="booking_cancel")
        cancel_booking()
        st.rerun()
    st.caption(ui["booking_note"])

# Example shortcuts, only before the first check.
# These are pills rather than buttons on purpose: a pills widget is one compact
# row by design, so there is no custom CSS involved and nothing to break on a
# small screen.
if st.session_state["phase"] in ("start", "check"):
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
booking_phase = st.session_state["phase"].startswith("book_")
typed = st.chat_input(ui["input_placeholder_booking" if booking_phase else "input_placeholder"])
if typed:
    typed = typed.strip()
    if typed:
        add("user", "text", text=typed)
        intent = intents.match(typed)
        booking_in_progress = st.session_state["phase"].startswith("book_") and intents.is_short(typed)
        if booking_in_progress and booking_reply(typed):
            pass
        elif booking_in_progress:
            # A question in the middle of a booking is answered, then the booking question is repeated.
            if intent:
                add("assistant", "text", intent=intent)
            booking_prompt()
        elif intents.is_greeting(typed):
            add("assistant", "text", ui="greeting_reply")
            if st.session_state["phase"] != "start":
                st.session_state["phase"] = "menu"
        elif intents.wants_booking(typed):
            start_booking()
        elif intent:
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
