"""The consultation booking demo: the calendar in backend/booking.py and the chat flow around it."""
from datetime import date, timedelta

import pytest

from backend import booking
from tests.test_frontend import fresh, press, say, switch_to_chinese, texts


@pytest.fixture(autouse=True)
def empty_calendar():
    booking.reset()
    yield
    booking.reset()


def button(app, key):
    return next(b for b in app.button if b.key == key)


def day_key(index):
    return f"day_{booking.open_days()[index].isoformat()}"


# ---- calendar ----------------------------------------------------------------

def test_open_days_are_the_next_five_working_days(monkeypatch):
    monkeypatch.setattr(booking, "today", lambda: date(2026, 11, 20))  # a Friday
    days = booking.open_days()
    assert days[0] == date(2026, 11, 23) and len(days) == 5
    assert all(day.weekday() < 5 for day in days)


def test_some_slots_start_booked_and_one_day_is_full():
    days = booking.open_days()
    assert "10:00" in booking.taken_times(days[0])
    assert booking.free_times(days[2]) == []
    assert booking.free_times(days[4]) == list(booking.SLOT_TIMES)


def test_a_slot_can_only_be_booked_once():
    day = booking.open_days()[4]
    reference = booking.book(day, "11:00")
    assert reference.startswith("SC-") and "11:00" not in booking.free_times(day)
    with pytest.raises(booking.SlotTaken):
        booking.book(day, "11:00")


def test_prebooked_and_unknown_slots_are_refused():
    days = booking.open_days()
    with pytest.raises(booking.SlotTaken):
        booking.book(days[0], "10:00")
    with pytest.raises(booking.UnknownSlot):
        booking.book(days[0], "12:30")
    with pytest.raises(booking.UnknownSlot):
        booking.book(days[0] - timedelta(days=30), "11:00")


@pytest.mark.parametrize("text,expected", [
    ("2pm", "14:00"), ("14:00", "14:00"), ("11am", "11:00"), ("下午兩點", "14:00"), ("十一點", "11:00"),
    ("晏晝3點", "15:00"), ("10.30", "10:30"), ("what is 18222", None), ("tuesday", None),
])
def test_times_are_understood(text, expected):
    assert booking.parse_time(text) == expected


def test_a_bare_number_is_a_time_only_when_asked_for_one():
    assert booking.parse_time("3") is None
    assert booking.parse_time("3", bare=True) == "15:00"
    assert booking.parse_time("what is 18222", bare=True) is None


def test_days_are_understood(monkeypatch):
    monkeypatch.setattr(booking, "today", lambda: date(2026, 11, 16))  # a Monday
    days = booking.open_days()
    assert booking.parse_day("Wednesday please", days) == date(2026, 11, 18)
    assert booking.parse_day("星期五", days) == date(2026, 11, 20)
    assert booking.parse_day("tomorrow", days) == date(2026, 11, 17)
    assert booking.parse_day("Saturday", days) is None


# ---- chat flow ---------------------------------------------------------------

def test_greeting_offers_the_two_functions():
    app = fresh()
    assert button(app, "menu_check") and button(app, "menu_book")
    say(app, "Hello!")
    assert "How can I help you today" in texts(app)
    assert "do not see a message" not in texts(app)


def test_a_message_that_starts_with_hi_is_still_checked():
    app = fresh()
    say(app, "Hi Mum, I will be home late tonight, see you at 6.")
    assert app.success and "How can I help you today" not in texts(app)


def test_check_a_message_button_asks_for_the_message():
    app = press(fresh(), "menu_check")
    assert "Paste the message you are worried about in the box below" in texts(app)
    app.pills[0].set_value("Bank").run()
    assert app.error


def test_booking_with_buttons():
    app = press(fresh(), "menu_book")
    assert "Which day would you like?" in texts(app)
    assert button(app, day_key(2)).disabled, "the fully booked day cannot be pressed"
    press(app, day_key(0))
    assert button(app, "time_1000").disabled and not button(app, "time_1100").disabled
    press(app, "time_1100")
    assert "Shall I book it?" in texts(app)
    press(app, "book_yes")
    body = texts(app)
    assert "Your consultation is booked" in body and "SC-" in body and "no real appointment" in body
    assert "11:00" in booking.taken_times(booking.open_days()[0])
    assert button(app, "menu_book"), "the menu comes back afterwards"


def test_a_booked_slot_is_taken_for_the_next_person():
    first = press(fresh(), "menu_book")
    press(first, day_key(4))
    press(first, "time_1500")
    press(first, "book_yes")
    second = press(fresh(), "menu_book")
    press(second, day_key(4))
    assert button(second, "time_1500").disabled


def test_booking_by_typing():
    app = fresh()
    weekday = booking.open_days()[0].strftime("%A")
    say(app, "I want to book a consultation")
    assert "Which day would you like?" in texts(app)
    say(app, f"{weekday} at 10am")
    assert "is already booked" in texts(app)
    say(app, "11am")
    assert "Shall I book it?" in texts(app)
    say(app, "yes")
    assert "Your consultation is booked" in texts(app)


def test_typing_a_full_day_or_an_odd_time_gets_a_clear_answer():
    app = press(fresh(), "menu_book")
    say(app, booking.open_days()[2].strftime("%A"))
    assert "is fully booked" in texts(app)
    say(app, booking.open_days()[1].strftime("%A"))
    say(app, "10:30")
    assert "start on the hour" in texts(app)
    say(app, "sometime")
    assert "did not catch the time" in texts(app)


def test_saying_no_goes_back_to_choosing_a_day():
    app = press(fresh(), "menu_book")
    press(app, day_key(1))
    press(app, "time_1000")
    press(app, "book_no")
    assert "Let us pick another time" in texts(app)
    assert button(app, day_key(1))
    assert booking.free_times(booking.open_days()[1])[0] == "10:00", "nothing was booked"


def test_cancel_by_typing_or_button():
    app = press(fresh(), "menu_book")
    say(app, "cancel")
    assert "Nothing was booked" in texts(app) and button(app, "menu_book")
    press(app, "menu_book")
    press(app, "cancel_booking")
    assert texts(app).count("Nothing was booked") == 2


def test_a_question_during_booking_is_answered_then_the_booking_continues():
    app = press(fresh(), "menu_book")
    say(app, "what is 18222")
    body = texts(app)
    assert "Anti-Scam Helpline" in body and "did not catch the day" in body
    assert button(app, day_key(0))


def test_a_scam_pasted_during_booking_is_still_checked():
    app = press(fresh(), "menu_book")
    say(app, "HSBC ALERT: A payment of $2,300 was detected. Confirm your identity now: http://hsbc-verify.top")
    assert app.error


def test_booking_in_chinese_and_language_switch():
    app = switch_to_chinese(fresh())
    say(app, "我想預約諮詢")
    assert "請問你想約哪一天" in texts(app)
    press(app, day_key(3))
    say(app, "下午三點")
    assert "已經有人預約" in texts(app)
    say(app, "下午兩點")
    say(app, "好")
    assert "已為你預約" in texts(app)
    app.radio[0].set_value("English").run()
    assert "Your consultation is booked" in texts(app) and "已為你預約" not in texts(app)
