from __future__ import annotations

from lse.metrics.factscore import factscore_heuristic, split_facts
from lse.metrics.length import length_stats, token_count


def test_token_count_basic() -> None:
    assert token_count("Hello, world!") == 2
    assert token_count("") == 0
    assert token_count("one two three four") == 4


def test_length_stats_ratios() -> None:
    s = length_stats(candidate="one two three", reference="one two", source="one two three four")
    assert s["cand_tokens"] == 3.0
    assert s["ref_tokens"] == 2.0
    assert s["source_tokens"] == 4.0
    assert s["length_ratio_vs_ref"] == 1.5
    assert s["compression_vs_source"] == 0.25


def test_split_facts_handles_multiple_sentences() -> None:
    facts = split_facts("Apples are red. Bananas are yellow. Cherries are sweet.")
    assert len(facts) == 3


def test_split_facts_empty() -> None:
    assert split_facts("") == []
    assert split_facts("   \n\n  ") == []


def test_factscore_high_when_summary_overlaps_source() -> None:
    src = "Apples are red. Bananas are yellow."
    summ = "Apples are red. Bananas are yellow."
    s = factscore_heuristic(summ, src, threshold=0.3)
    assert s["factscore_p"] == 1.0


def test_factscore_low_when_summary_is_off_topic() -> None:
    src = "Apples are red and crunchy."
    summ = "The capital of France is Paris."
    s = factscore_heuristic(summ, src, threshold=0.3)
    assert s["factscore_p"] == 0.0


def test_factscore_empty_summary() -> None:
    s = factscore_heuristic("", "any source", threshold=0.3)
    assert s["factscore_p"] == 0.0
    assert s["n_facts"] == 0
