"""Routing for Q3 ("unusual transactions"): detect the question so src.app can use the
deterministic rules in src/data_layer/anomaly.py instead of LLM-written SQL."""
import re

_UNUSUAL = re.compile(r"\b(unusual|anomal\w*|suspicious|outlier\w*|duplicate\w*)\b", re.IGNORECASE)


def is_anomaly_question(question: str) -> bool:
    return bool(_UNUSUAL.search(question))
