"""Trained text classifiers (see ml/train.py). They add one signal to the risk score.

English and Chinese each have their own model. If a model is missing or the text has no known term,
there is no signal instead of a meaningless probability, and the rest of the app carries on without it.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)


def _path(language: str) -> Path:
    return config.ZH_CLASSIFIER_PATH if language == "zh" else config.CLASSIFIER_PATH


@lru_cache(maxsize=2)
def _model(language: str):
    if not _path(language).exists():
        return None
    try:
        import joblib
        return joblib.load(_path(language))
    except Exception:
        logger.warning("Classifier for %s could not be loaded; run ml.train again", language, exc_info=True)
        return None


def is_ready(language: str = "en") -> bool:
    return _model(language) is not None


def scam_probability(text: str, language: str) -> float | None:
    """Probability from 0 to 1, or None when there is no model or no basis for an answer."""
    model = _model(language)
    if model is None or model.named_steps["tfidf"].transform([text]).nnz == 0:
        return None
    return float(model.predict_proba([text])[0, 1])
