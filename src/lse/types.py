"""Core types: a summarization sample = (source doc, reference summary, candidate summary)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SummSample:
    sid: str
    source: str
    reference: str
    candidate: str
    cited_sources: tuple[str, ...] = ()  # optional citations inside candidate


@dataclass
class ScoreRow:
    sid: str
    metrics: dict[str, float] = field(default_factory=dict)
    candidate_len_tokens: int = 0
    reference_len_tokens: int = 0
