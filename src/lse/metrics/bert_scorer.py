"""BERTScore wrapper.

We use bert-score's `bert_score.score(...)` helper with a small backbone
(`roberta-large` by default; switch to `microsoft/deberta-xlarge-mnli` for
the published-paper config). For CPU-friendly use, swap to
`distilbert-base-uncased` via the `model_type` kwarg.

Returns precision, recall, F1 (averaged across the batch if you pass lists).
"""

from __future__ import annotations

from typing import Any


def bert_score_one(
    candidate: str,
    reference: str,
    model_type: str = "distilbert-base-uncased",
) -> dict[str, float]:
    from bert_score import score as bscore

    p, r, f = bscore(
        cands=[candidate],
        refs=[reference],
        model_type=model_type,
        lang="en",
        verbose=False,
        rescale_with_baseline=False,
    )
    return {
        "bertscore_p": float(p[0]),
        "bertscore_r": float(r[0]),
        "bertscore_f": float(f[0]),
    }


def bert_score_batch(
    candidates: list[str],
    references: list[str],
    model_type: str = "distilbert-base-uncased",
) -> list[dict[str, float]]:
    from bert_score import score as bscore

    p, r, f = bscore(
        cands=candidates,
        refs=references,
        model_type=model_type,
        lang="en",
        verbose=False,
        rescale_with_baseline=False,
    )
    out: list[dict[str, Any]] = []
    for i in range(len(candidates)):
        out.append(
            {
                "bertscore_p": float(p[i]),
                "bertscore_r": float(r[i]),
                "bertscore_f": float(f[i]),
            }
        )
    return out
