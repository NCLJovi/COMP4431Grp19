"""
speech.py — turning the warning into sound
==========================================
Requirement F5: voice output. The user must be able to *hear* the warning,
because a frightened 80-year-old may not read a screen carefully.

How it works
------------
Windows ships with speech voices. `speech.ps1` asks one of them to write a
.wav file, and streamlit_app.py hands those bytes to Streamlit's audio player.

No account, no API key, no internet, no cost — which matters for requirement
N10 and for a demo room with bad Wi-Fi.

On a Mac or Linux machine this returns None and streamlit_app.py simply does not show
the player. Nothing breaks; the warning is still readable.
"""

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = HERE / "speech.ps1"

# Synthesising takes about a second, so keep the last few results in memory.
_CACHE = {}
_CACHE_LIMIT = 8

# If the first attempt fails, do not try again on every rerun: that would add
# a delay to every screen for the rest of the session. Tracked per language, because
# a computer can have an English voice and no Chinese one.
_BROKEN = set()

TIMEOUT_SECONDS = 10


def available(language="en"):
    """True if this machine can speak this language."""
    return os.name == "nt" and SCRIPT.exists() and language not in _BROKEN


def spoken_text(template):
    """What we actually say out loud.

    Not the whole screen: the verdict and the first two instructions.
    Reading every line aloud would take 40 seconds and nobody would listen.
    """
    headline = template["headline"]
    steps = template["steps"][:2]
    return " ".join([headline] + steps)


def synthesize(text, language="en"):
    """Return WAV bytes for `text`, or None if this machine cannot speak this language."""
    if not available(language):
        return None

    key = hashlib.sha256(f"{language}:{text}".encode("utf-8")).hexdigest()
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    text_file = None
    wave_file = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(text)
            text_file = handle.name

        wave_file = text_file.replace(".txt", ".wav")

        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-File", str(SCRIPT),
                "-TextFile", text_file,
                "-WaveFile", wave_file,
                "-Culture", language,
            ],
            # No pipes: some managed Windows environments refuse to let a
            # child process write to a pipe, and we do not need its output.
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT_SECONDS,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        if completed.returncode != 0 or not os.path.exists(wave_file):
            _BROKEN.add(language)
            return None

        with open(wave_file, "rb") as handle:
            audio = handle.read()
    except Exception:
        _BROKEN.add(language)
        return None
    finally:
        for path in (text_file, wave_file):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    if len(_CACHE) >= _CACHE_LIMIT:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = audio
    return audio


if __name__ == "__main__":
    # Quick check: run `python speech.py` and it writes spoken_test.wav here.
    sample = (
        "This looks like a scam. Do not reply, and do not click any link. "
        "Do not send money, a password, or any code."
    )
    audio = synthesize(sample)
    if audio is None:
        print("No speech available on this machine.")
    else:
        out = HERE / "spoken_test.wav"
        out.write_bytes(audio)
        print(f"Wrote {out.name}: {len(audio)} bytes, about {len(audio) / 32000:.1f} seconds")
