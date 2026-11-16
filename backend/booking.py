"""Consultation booking demo.

Bookings are kept in memory only: they are shared by everyone using the running app, they disappear
when the app restarts, and no real appointment is made. Some slots are marked as already booked so
the chatbot can show what happens when a time is not available.
"""
from __future__ import annotations

import re
import secrets
import threading
from datetime import date, datetime, timedelta, timezone

HONG_KONG = timezone(timedelta(hours=8))  # Hong Kong has no daylight saving time
SLOT_TIMES = ("10:00", "11:00", "14:00", "15:00", "16:00")
OPEN_DAYS = 5  # the next five working days

# Slots that are already taken, by position in the list of open days (0 = the next working day).
# Day 2 is fully booked on purpose.
PREBOOKED = {
    0: {"10:00", "14:00"},
    1: {"11:00"},
    2: set(SLOT_TIMES),
    3: {"15:00"},
}

MAX_BOOKINGS = 200


class SlotTaken(Exception):
    """Someone already has this slot."""


class UnknownSlot(ValueError):
    """The day or time is not one that can be booked."""


_lock = threading.Lock()
_bookings: dict[tuple[date, str], str] = {}  # (day, time) -> reference


def today() -> date:
    return datetime.now(HONG_KONG).date()


def open_days() -> list[date]:
    """The next working days, starting tomorrow."""
    day, days = today(), []
    while len(days) < OPEN_DAYS:
        day += timedelta(days=1)
        if day.weekday() < 5:
            days.append(day)
    return days


def taken_times(day: date) -> set[str]:
    days = open_days()
    if day not in days:
        raise UnknownSlot(f"{day} is not open for booking")
    return set(PREBOOKED.get(days.index(day), ())) | {time for booked_day, time in _bookings if booked_day == day}


def free_times(day: date) -> list[str]:
    taken = taken_times(day)
    return [time for time in SLOT_TIMES if time not in taken]


def book(day: date, time: str) -> str:
    """Books the slot and returns a reference such as SC-4821."""
    if time not in SLOT_TIMES:
        raise UnknownSlot(f"{time} is not a consultation time")
    with _lock:
        if time in taken_times(day):
            raise SlotTaken(f"{day} {time}")
        for key in [key for key in _bookings if key[0] < today()]:
            del _bookings[key]
        if len(_bookings) >= MAX_BOOKINGS:
            raise SlotTaken("the demo calendar is full")
        reference = f"SC-{secrets.randbelow(9000) + 1000}"
        _bookings[(day, time)] = reference
        return reference


def reset() -> None:
    """Forget every booking made since the app started. Used by the tests."""
    with _lock:
        _bookings.clear()


# ---------------------------------------------------------------------------
# Understanding what the user typed
# ---------------------------------------------------------------------------
_WEEKDAY_NAMES = (
    (r"\bmon(?:day)?\b", "星期一", "禮拜一", "週一", "周一"),
    (r"\btue(?:s|sday)?\b", "星期二", "禮拜二", "週二", "周二"),
    (r"\bwed(?:nesday)?\b", "星期三", "禮拜三", "週三", "周三"),
    (r"\bthu(?:r|rs|rsday)?\b", "星期四", "禮拜四", "週四", "周四"),
    (r"\bfri(?:day)?\b", "星期五", "禮拜五", "週五", "周五"),
)
_TOMORROW = re.compile(r"\btomorrow\b|明天|明日|聽日", re.IGNORECASE)
_CHINESE_NUMBERS = {"十二": 12, "十一": 11, "十": 10, "一": 1, "二": 2, "兩": 2, "两": 2, "三": 3, "四": 4,
                    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_TIME = re.compile(
    r"(?P<before>上午|下午|晏晝|朝早|早上)?\s*"
    r"(?P<hour>\d{1,2}|十二|十一|十|[一二兩两三四五六七八九])\s*"
    r"(?:(?P<colon>[:：.])\s*(?P<minute>\d{2})|(?P<dot>[點点時时])(?:正|鐘|钟)?)?\s*"
    r"(?P<after>a\.?m\.?|p\.?m\.?)?",
    re.IGNORECASE,
)


def parse_day(text: str, days: list[date]) -> date | None:
    """Finds a weekday name or "tomorrow" in the text. Returns None if it is not one of `days`."""
    if _TOMORROW.search(text):
        tomorrow = today() + timedelta(days=1)
        return tomorrow if tomorrow in days else None
    for day in days:
        if any(re.search(name, text, re.IGNORECASE) for name in _WEEKDAY_NAMES[day.weekday()]):
            return day
    return None


def parse_time(text: str, bare: bool = False) -> str | None:
    """Finds a time such as "2pm", "14:00" or "下午兩點" and returns it as "14:00".

    A number on its own, such as "3", only counts when `bare` is true and it is the only number in a
    short reply. Hours from 1 to 7 without am or pm are taken as afternoon, because the desk opens at 10.
    """
    for match in _TIME.finditer(text):
        marked = any(match.group(name) for name in ("before", "colon", "dot", "after"))
        if not marked and not (bare and len(text) <= 12 and len(re.findall(r"\d+", text)) <= 1):
            continue
        raw = match.group("hour")
        hour = _CHINESE_NUMBERS.get(raw) or int(raw)
        afternoon = (match.group("before") in ("下午", "晏晝")) or (match.group("after") or "").lower().startswith("p")
        morning = (match.group("before") in ("上午", "朝早", "早上")) or (match.group("after") or "").lower().startswith("a")
        if hour < 12 and (afternoon or (not morning and 1 <= hour <= 7)):
            hour += 12
        if hour > 23:
            continue
        return f"{hour:02d}:{match.group('minute') or '00'}"
    return None
