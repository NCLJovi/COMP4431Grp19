"""Connects the Streamlit app to the scam detector.

By default the app runs the detector inside its own process, so a single Streamlit Community Cloud
deployment is enough. Set the SCAM_API_URL environment variable to call a separately hosted API instead,
for example http://127.0.0.1:8000/analyze.

The returned dict always follows docs/API_CONTRACT.md.
"""

import asyncio
import os

import requests

TIMEOUT_SECONDS = 3


class AnalysisError(Exception):
    """Raised when the message could not be checked at all."""


def _call_api(message, url):
    response = requests.post(url, json={"message": message}, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _call_detector(message):
    # Imported here so that the first page load is not held up by the model.
    from backend.service import check_message

    return asyncio.run(check_message(message)).model_dump()


def analyze(message):
    """Check one message and return the agreed dict."""
    url = os.getenv("SCAM_API_URL", "").strip()
    try:
        return _call_api(message, url) if url else _call_detector(message)
    except Exception as error:
        # Never let a detector problem turn into a broken screen.
        raise AnalysisError("The checking service is not answering.") from error
