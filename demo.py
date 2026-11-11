"""Terminal demo that follows the presentation script. It runs in-process, so no server is needed.

  python demo.py            menu
  python demo.py --auto     every scene, without pausing
  python demo.py --no-llm   use template explanations, for a slow laptop
  python demo.py --audio call.wav   use a real recording in scene 2 (needs faster-whisper)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from backend import dialogue, gym, stt
from backend.config import DATA_DIR, RESULTS_DIR

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

console = Console()
LEVEL_STYLE = {"low": "green", "medium": "yellow", "high": "bold red"}
AVATAR = {
    "low": "  .---.\n ( ^ ^ )\n (  u  )  All clear\n  '---'",
    "medium": "  .---.\n ( o - )\n (  ~  )  Hmm, be careful\n  '---'",
    "high": "  .---.   /!\\\n ( > < ) /___\\\n (  O  )  Stop! Do not pay!\n  '---'",
}
PARCEL_SMS = "SF Express: your parcel could not be delivered because the address is incomplete. Update it within 24 hours or it will be returned: https://sf-express-hk.top/track"
CANTONESE_SMS = "【滙豐】閣下戶口出現異常，已被凍結。請立即登入 hsbc-hk-login.top 核實身份，並回覆驗證碼。"


def highlighted(text: str, rules: list) -> Text:
    output = Text(text)
    for rule in rules:
        if rule.span:
            output.stylize("black on spring_green2" if rule.weight < 0 else "black on orange1", *rule.span)
    return output


def show_next_steps(response) -> None:
    if response.action_plan:
        steps = "\n".join(f"{i}. {s}" for i, s in enumerate(response.action_plan.steps, 1))
        console.print(Panel(steps, title=f"Action plan ({response.action_plan.urgency})", border_style="red" if response.action_plan.urgency == "critical" else "blue"))
    if response.incident_summary:
        console.print(Panel(response.incident_summary, title="Incident summary for the bank or police"))
    if response.next_question:
        console.print(f"[bold cyan]Bot asks:[/bold cyan] {response.next_question}")


def show(response, text: str | None = None) -> None:
    style = LEVEL_STYLE[response.risk_level]
    filled = response.risk_score // 4
    meter = Text()
    meter.append("Risk ", style="bold")
    meter.append("#" * filled, style=style)
    meter.append("-" * (25 - filled), style="dim")
    meter.append(f" {response.risk_score}/100 {response.risk_level.upper()}", style=style)
    console.print(Text(AVATAR[response.risk_level], style=style))
    console.print(meter)
    b = response.score_breakdown
    if b:
        console.print(f"[dim]Score = rules {b['rules']} + similar case {b['similar_case']} + URL {b['url']} + classifier {b['classifier']}[/dim]")
    if response.scam_probability is not None:
        console.print(f"[magenta]Trained classifier (TF-IDF + logistic regression):[/magenta] P(spam) = {response.scam_probability:.0%}")
    if text:
        console.print(Panel(highlighted(text, response.triggered_rules), title="Message (orange = red flag, green = safe sign)"))
    if response.triggered_rules:
        table = Table(title="Red flags", show_lines=False)
        for column in ("Rule", "Name", "Weight", "Why"):
            table.add_column(column, overflow="fold")
        seen = set()
        for rule in response.triggered_rules:
            if rule.id not in seen and rule.id != "U1":
                seen.add(rule.id)
                table.add_row(rule.id, f"{rule.name} {rule.name_zh}", f"{rule.weight:g}", rule.why)
        console.print(table)
    if response.inference_trace:
        console.print(Panel("\n".join(response.inference_trace), title="Forward chaining"))
    for finding in response.url_findings:
        if finding.issue:
            target = f" imitating [bold]{finding.target}[/bold]" if finding.target else ""
            console.print(f"[red]URL Inspector:[/red] {finding.url} -> {finding.issue}{target}")
    for case in response.similar_cases[:1]:
        console.print(f"[cyan]Similar case:[/cyan] {case.title} ({case.similarity:.0%})")
    source = "local LLM" if response.explanation_source == "llm" else "template"
    console.print(Panel(response.explanation, title=f"Explanation ({source})", border_style=style))
    show_next_steps(response)


def say(session, message: str, use_llm: bool, follow_up: bool = False, echo: bool = True):
    if echo:
        console.print(f"\n[bold]User:[/bold] {message}")
    with console.status("Analysing..."):
        response = asyncio.run(dialogue.chat(session, message, use_llm=use_llm))
    if follow_up:
        console.print(Panel(response.explanation, border_style=LEVEL_STYLE[response.risk_level]))
        show_next_steps(response)
    else:
        show(response, message)
    return response


def scene_sms(use_llm: bool, **_) -> None:
    console.rule("Scene 1: suspicious SMS")
    say(dialogue.get_session(None), PARCEL_SMS, use_llm)


def scene_call(use_llm: bool, audio: str | None, state: dict, **_) -> None:
    console.rule("Scene 2: phone recording")
    session = dialogue.get_session(None)
    state["call_session"] = session
    if audio:
        with open(audio, "rb") as f, console.status("Transcribing..."):
            transcript = stt.transcribe(f.read())
    else:
        console.print("[dim]Using the prepared transcript. Pass --audio call.wav to transcribe a recording.[/dim]")
        transcript = (DATA_DIR / "demo" / "fake_immigration_call.txt").read_text(encoding="utf-8").strip()
    say(session, transcript, use_llm, echo=False)


def scene_paid(use_llm: bool, state: dict, **_) -> None:
    console.rule("Scene 3: the victim has already paid")
    session = state.get("call_session")
    if session is None:
        scene_call(use_llm, None, state)
        session = state["call_session"]
    say(session, "I already transferred HK$50,000", use_llm, follow_up=True)


def scene_gym(auto: bool, **_) -> None:
    console.rule("Scene 4: Scam Gym")
    turn = gym.start("bank")
    console.print(Panel(turn["banner"], style="black on yellow"))
    scripted = iter(["Is this a scam? I will not give you anything.", "I will call the bank using the number on my card.", "I am hanging up now."])
    while True:
        console.print(f"[red]Scammer (training):[/red] {turn['scammer']}")
        reply = next(scripted) if auto else console.input("[bold]Your reply:[/bold] ").strip() or "..."
        if auto:
            console.print(f"[bold]Your reply:[/bold] {reply}")
        turn = gym.reply(turn["session_id"], reply)
        for line in turn["feedback"]:
            console.print(f"[green]Coach:[/green] {line}")
        if turn["finished"]:
            break
    report = turn["report"]
    body = [f"Score: {report['score']}/100 ({report['grade']})"]
    body += [f"+ {x}" for x in report["did_well"]] + [f"- {x}" for x in report["mistakes"]] + [report["tip"]]
    console.print(Panel("\n".join(body), title="Training report"))


def scene_eval(**_) -> None:
    console.rule("Scene 5: evaluation")
    path = RESULTS_DIR / "metrics.json"
    if not path.exists():
        console.print("Run python -m ga.tune and python -m evaluation.run_eval first.")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {"rule_only": "Rule-only", "classifier_only": "Classifier-only", "classifier_only_english": "Classifier-only (English messages)",
             "hybrid": "Hybrid (rules + URL + similar case)", "hybrid_ga": "Hybrid + GA weights",
             "hybrid_ga_classifier": "Hybrid + GA + classifier", "llm_only": "LLM-only"}
    for title, rows in (("5-fold cross-validation", data["cross_validation"]["summary"]), (f"Held-out test ({sum(data['test']['hybrid'][k] for k in ('tp', 'fp', 'fn', 'tn'))} messages)", data["test"])):
        table = Table(title=title)
        for column in ("Method", "Accuracy", "Precision", "Recall", "F1"):
            table.add_column(column)
        for key, m in rows.items():
            table.add_row(names[key], str(m["accuracy"]), str(m["precision"]), str(m["recall"]), str(m["f1"]))
        console.print(table)
    console.print(f"Rule engine response time: p50 {data['latency']['p50_ms']} ms, p95 {data['latency']['p95_ms']} ms")
    console.print(f"[yellow]Caution: {data['warning']}[/yellow]")


def scene_cantonese(use_llm: bool, **_) -> None:
    console.rule("Bonus: Cantonese message")
    say(dialogue.get_session(None), CANTONESE_SMS, use_llm)


SCENES = [("Suspicious SMS", scene_sms), ("Phone recording", scene_call), ("Already paid", scene_paid),
          ("Scam Gym", scene_gym), ("Evaluation", scene_eval), ("Cantonese message", scene_cantonese)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Scam Checker terminal demo")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--audio")
    args = parser.parse_args()
    options = {"use_llm": not args.no_llm, "auto": args.auto, "audio": args.audio, "state": {}}

    if args.auto:
        for _, scene in SCENES:
            scene(**options)
        return
    while True:
        console.rule("Scam Checker demo")
        for i, (name, _) in enumerate(SCENES, 1):
            console.print(f"  {i}. {name}")
        console.print("  a. Run all    t. Type your own message    q. Quit")
        choice = console.input("Choose: ").strip().lower()
        if choice == "q":
            return
        if choice == "a":
            for _, scene in SCENES:
                scene(**options)
                console.input("[dim]Press Enter to continue[/dim]")
        elif choice == "t":
            session = dialogue.get_session(None)
            while message := console.input("[bold]Message (empty to stop):[/bold] ").strip():
                say(session, message, options["use_llm"], echo=False)
        elif choice.isdigit() and 1 <= int(choice) <= len(SCENES):
            SCENES[int(choice) - 1][1](**options)


if __name__ == "__main__":
    main()
