"""ROUGE-1/2/L F-measure wrapper.

The rouge-score package is the standard reference impl (matches the published
ROUGE values closely). We just expose a single-call helper that returns the
three F1 numbers in one shot.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rouge_score.rouge_scorer import RougeScorer

_SCORER: RougeScorer | None = None


def _scorer() -> RougeScorer:
    global _SCORER
    if _SCORER is None:
        from rouge_score.rouge_scorer import RougeScorer

        _SCORER = RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    return _SCORER


def rouge(candidate: str, reference: str) -> dict[str, float]:
    s = _scorer().score(target=reference, prediction=candidate)
    return {
        "rouge1_f": float(s["rouge1"].fmeasure),
        "rouge2_f": float(s["rouge2"].fmeasure),
        "rougeL_f": float(s["rougeL"].fmeasure),
    }
