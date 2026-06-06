from __future__ import annotations

from pathlib import Path

from lse.runner import load_jsonl

FIX = Path(__file__).parent / "fixtures"


def test_load_billsum_mini() -> None:
    samples = load_jsonl(FIX / "billsum_mini.jsonl")
    assert len(samples) == 6
    assert samples[0].sid == "b1"
    assert "Senior Medical" in samples[0].source
    assert "Senior Medical" in samples[0].candidate


def test_sample_immutable() -> None:
    samples = load_jsonl(FIX / "billsum_mini.jsonl")
    try:
        samples[0].sid = "x"  # type: ignore[misc]
    except (AttributeError, TypeError):
        return
    raise AssertionError("Sample should be frozen")
