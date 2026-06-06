"""FActScore-lite: atomic-fact precision against the source document.

Real FActScore (Min et al., 2023) uses an LLM to decompose the summary into
atomic facts, then a knowledge-source verifier to label each as supported.
We ship two variants:

  - factscore_heuristic : split the summary on sentences (atomic-fact proxy),
                          mark each as supported if it has high token overlap
                          with the source. Fast, no LLM needed.
  - factscore_nli       : same decomposition, but uses an NLI head to compute
                          P(source entails fact). More accurate, slower.

We return precision = supported / total facts. Recall is not defined here
because the source contains many facts the summary may legitimately omit.
"""

from __future__ import annotations

import re

_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def split_facts(summary: str) -> list[str]:
    summary = summary.strip()
    if not summary:
        return []
    out: list[str] = []
    for chunk in summary.splitlines():
        chunk = chunk.strip()
        if not chunk:
            continue
        out.extend(s.strip() for s in _SENT.split(chunk) if s.strip())
    return out


_WORD = re.compile(r"\w+")


def _toks(text: str) -> set[str]:
    return {t for t in (m.group(0).lower() for m in _WORD.finditer(text)) if len(t) > 2}


def factscore_heuristic(summary: str, source: str, threshold: float = 0.3) -> dict[str, float]:
    facts = split_facts(summary)
    if not facts:
        return {"factscore_p": 0.0, "n_facts": 0, "n_supported": 0}
    src_toks = _toks(source)
    if not src_toks:
        return {"factscore_p": 0.0, "n_facts": float(len(facts)), "n_supported": 0}
    supported = 0
    for f in facts:
        f_toks = _toks(f)
        if not f_toks:
            continue
        coverage = len(f_toks & src_toks) / len(f_toks)
        if coverage >= threshold:
            supported += 1
    return {
        "factscore_p": supported / len(facts),
        "n_facts": float(len(facts)),
        "n_supported": float(supported),
    }
