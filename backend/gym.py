"""Scam Gym, a scripted training mode. The fictional scripts and the feedback text are in backend/wording.py."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from . import wording

_UNSAFE = re.compile(r"\b(?:ok|okay|sure|yes|here(?:'s| is)|my (?:otp|card|password|pin|number)|i(?:'ll| will) (?:pay|transfer|send|click)|the code is)\b|好啦|好呀|可以|俾你|畀你|即刻過數|我過數|我撳|驗證碼係|密碼係|\d{4,}", re.IGNORECASE)
_SAFE = {
    wording.GYM_SKILLS["refused"]: r"\b(?:no|never|won't|will not|refuse|not giving|don't give)\b|唔會俾|唔俾|不會|唔得|拒絕",
    wording.GYM_SKILLS["checked"]: r"\b(?:call (?:the|my) bank|official|verify|check with|number on (?:my|the) card|branch|18222)\b|打俾銀行|打去銀行|官方|查證|分行|卡背|18222",
    wording.GYM_SKILLS["recognised"]: r"\b(?:scam|fake|fraud|suspicious|police|report)\b|騙|假|報警",
    wording.GYM_SKILLS["ended"]: r"\b(?:hang up|hanging up|bye|block|delete|ignore)\b|收線|封鎖|刪除|唔理",
    wording.GYM_SKILLS["told_family"]: r"\b(?:my (?:son|daughter|family|children)|ask (?:my )?family)\b|屋企人|仔女|家人",
}
_SAFE_COMPILED = {k: re.compile(v, re.IGNORECASE) for k, v in _SAFE.items()}


@dataclass
class GymSession:
    id: str
    scenario: str
    step: int = 0
    score: int = 50
    good: list[str] = field(default_factory=list)
    mistakes: list[str] = field(default_factory=list)


_gym_sessions: dict[str, GymSession] = {}


def start(scenario: str = "bank") -> dict:
    if scenario not in wording.GYM_SCENARIOS:
        raise KeyError(scenario)
    session = GymSession(uuid.uuid4().hex, scenario)
    _gym_sessions[session.id] = session
    return {"session_id": session.id, "banner": wording.GYM_BANNER, "title": wording.GYM_SCENARIOS[scenario]["title"],
            "scammer": wording.GYM_SCENARIOS[scenario]["lines"][0], "finished": False}


def _report(session: GymSession) -> dict:
    score = max(0, min(100, session.score))
    grade = wording.GYM_GRADES["top" if score >= 85 else "middle" if score >= 65 else "bottom"]
    return {"score": score, "grade": grade, "did_well": session.good, "mistakes": session.mistakes,
            "tip": wording.GYM_FEEDBACK["tip"]}


def reply(session_id: str, text: str) -> dict:
    session = _gym_sessions[session_id]
    lines = wording.GYM_SCENARIOS[session.scenario]["lines"]
    feedback = []
    if _UNSAFE.search(text) and not any(p.search(text) for p in _SAFE_COMPILED.values()):
        session.score -= 30
        session.mistakes.append(wording.GYM_FEEDBACK["mistake"].format(step=session.step + 1))
        feedback.append(wording.GYM_FEEDBACK["unsafe"])
    for label, pattern in _SAFE_COMPILED.items():
        if pattern.search(text) and label not in session.good:
            session.good.append(label)
            session.score += 10
            feedback.append(wording.GYM_FEEDBACK["good"].format(skill=label.lower()))
    session.step += 1
    result = {"session_id": session.id, "banner": wording.GYM_BANNER, "feedback": feedback}
    if session.step >= len(lines):
        del _gym_sessions[session_id]
        return {**result, "finished": True, "scammer": None, "report": _report(session)}
    return {**result, "finished": False, "scammer": lines[session.step]}
