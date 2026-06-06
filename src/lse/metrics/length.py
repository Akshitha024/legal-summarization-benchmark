"""Length-only metrics. Cheap but they catch the common 'summary is just a
verbatim quote of the source' failure mode that ROUGE can mistakenly reward.
"""

from __future__ import annotations

import re

_WORD = re.compile(r"\w+")


def token_count(text: str) -> int:
    return len(_WORD.findall(text))


def length_stats(candidate: str, reference: str, source: str) -> dict[str, float]:
    c = token_count(candidate)
    r = token_count(reference)
    s = token_count(source)
    return {
        "cand_tokens": float(c),
        "ref_tokens": float(r),
        "source_tokens": float(s),
        "compression_vs_source": (1.0 - c / s) if s else 0.0,
        "length_ratio_vs_ref": (c / r) if r else 0.0,
    }
