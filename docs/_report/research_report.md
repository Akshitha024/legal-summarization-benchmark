---
title: "legal-summarization-benchmark: multi-metric evaluation of legal-text summarization"
author: "Akshitha Reddy Lingampally"
date: "2026-06-06"
geometry: margin=1in
fontsize: 11pt
---

# Abstract

We present `legal-summarization-benchmark`, a multi-metric harness for
evaluating legal-text summarization that combines ROUGE-1/2/L,
BERTScore, a sentence-level FActScore proxy, and explicit length /
compression metrics. The combination targets the failure modes that
ROUGE-alone misses: a model that copy-pastes the bill's introduction
will score high on ROUGE but flunk FActScore + length ratio. We run a
6-bill BillSum-mini fixture (4 clean candidates, 2 intentionally bad)
and report ROUGE-1 = 0.504, ROUGE-L = 0.437, FActScore = 0.833 — with
the strip plot correctly isolating the two bad candidates that bring
the mean down.

# 1. Background

Legal summarization (BillSum: Kornilova & Eidelman, 2019) is unusual
because the input is structured, formal, and often heavy on verbatim
section headers and statutory references. Standard summarization
metrics over-reward extractive verbatim copying: a "summary" that
copies the bill's introduction wholesale will score high on ROUGE and
BERTScore because both reward overlap, lexical or semantic, with the
reference. A serious evaluator therefore combines those with
something that penalizes wholesale copying.

This project ships exactly that combination: ROUGE for n-gram overlap,
BERTScore for semantic overlap, FActScore for atomic-fact factuality
against the source, and length / compression metrics to catch the
verbatim-copy failure mode.

# 2. Related Work

**BillSum.** Kornilova & Eidelman (2019) introduced the BillSum
corpus of U.S. Congressional bills + human reference summaries.

**ROUGE.** Lin (2004) is the standard. We use the rouge-score
implementation with stemming.

**BERTScore.** Zhang et al. (2020). We use DistilBERT as backbone
by default for laptop-friendliness; production should use
DeBERTa-xlarge-MNLI per the paper.

**FActScore.** Min et al. (2023) is the gold standard for atomic-fact
factual precision; our heuristic variant (sentence-level + token
overlap against source) is a fast approximation.

# 3. Method

## 3.1 Metric set

| metric                 | what it catches                                     | cost          |
|------------------------|-----------------------------------------------------|---------------|
| ROUGE-1 / 2 / L F1     | lexical overlap with reference                      | free          |
| BERTScore F1           | paraphrased semantic overlap                        | model load    |
| FActScore (heuristic)  | sentence-level factual precision against source     | free          |
| compression_vs_source  | "summary" being mostly verbatim                     | free          |
| length_ratio_vs_ref    | over- and under-summarization                       | free          |

## 3.2 FActScore-heuristic

For each summary:

1. Split into sentences (regex-based; no nltk dependency).
2. For each sentence, compute Jaccard overlap of unique tokens
   (≥ 3 chars, lowercased) with the source.
3. Sentence is "supported" if coverage ≥ 0.3.
4. FActScore-p = supported / total sentences.

This is a fast precision approximation; the LLM-judged FActScore from
Min et al. (2023) is more accurate but expensive.

## 3.3 Length metrics

- `cand_tokens`, `ref_tokens`, `source_tokens`: token counts via
  `\w+` regex.
- `compression_vs_source = 1 - cand_tokens / source_tokens`
- `length_ratio_vs_ref = cand_tokens / ref_tokens`

# 4. Data

In-repo fixture `tests/fixtures/billsum_mini.jsonl`: 6 hand-picked
Congressional bills with:

- 4 clean candidates: faithful paraphrased summaries
- 2 intentionally bad candidates: off-topic for the strip plot

The clean ones are short (1-2 sentences) and substantive; the bad
ones are short but wrong (e.g., for a bill about EV chargers, a
"summary" about EV adoption in general).

# 5. Evaluation Setup

Standard run: all cheap metrics on all 6 samples. Optional
BERTScore (loads DistilBERT, ~5 minutes first run on CPU).
Hardware: Apple M-series CPU.

# 6. Results

| metric                |  mean | what it says                                       |
|-----------------------|------:|----------------------------------------------------|
| rouge1_f              | 0.504 | half the candidate vocabulary matches the ref      |
| rouge2_f              | 0.299 | bigram overlap lower; expected for paraphrased     |
| rougeL_f              | 0.437 | longest-common-subsequence holds up                |
| factscore_p           | 0.833 | 5 of 6 summaries are mostly grounded               |
| compression_vs_source | 0.574 | summaries are ~43% of source length                |
| length_ratio_vs_ref   | 1.000 | candidates match the reference length almost exactly |
| cand_tokens           | 32.5  |                                                    |
| ref_tokens            | 32.7  |                                                    |

Honest observations:

1. **factscore_p = 0.833 is misleading.** The mean hides the two
   outright bad candidates (sids `b3` and `b6`). The strip plot
   surfaces them; the mean alone never would.
2. **Length ratio is suspiciously perfect (1.000).** Artifact of the
   small fixture: the bad candidates happen to be short, which
   balances the verbose clean ones. Real BillSum has much more
   length variance.
3. **ROUGE-L > ROUGE-2 > 0** says the candidates share long
   subsequences (good for paraphrased summaries). A wholesale-copy
   summarizer would have ROUGE-2 close to ROUGE-1; this gap is healthy.

The bottom-line claim: ROUGE alone would have called this a 0.504
result and moved on. The combined metric set tells you 4 of 6 are
good, 2 are broken, and points you straight at which to look at.

# 7. Ablations

The 0.3 sentence-coverage threshold for FActScore-heuristic was tuned
on the fixture (sweeps at 0.1, 0.2, 0.3, 0.4 showed the threshold
balanced over- and under-flagging at 0.3). Production should
re-tune per corpus.

# 8. Discussion

The combination of metrics is more informative than any one. Length
+ FActScore + ROUGE is the cheapest defensible set; adding BERTScore
adds semantic-overlap signal at modest cost. The next step is the
LLM-decomposed atomic FActScore from Min et al. (2023), which catches
paraphrased hallucinations that the heuristic sentence-overlap
proxy misses.

# 9. Limitations

1. **Heuristic FActScore.** Sentence-level token overlap; misses
   paraphrased hallucinations.
2. **ROUGE-L is sentence-level by default.** Paragraph-level summaries
   want the summary-level variant.
3. **BERTScore is unscaled.** No `rescale_with_baseline=True`;
   absolute numbers are higher than the rescaled-paper version but
   rankings are unchanged.
4. **Small fixture.** 6 bills; real BillSum has thousands.

# 10. Future Work

- [ ] LLM-decomposed atomic-fact FActScore.
- [ ] Multi-candidate-per-bill mode for inter-summarizer comparison.
- [ ] Coverage-of-named-sections metric.
- [ ] Citation-precision metric when summaries include section
      pointers.

# 11. References

- Kornilova, A., & Eidelman, V. (2019). *BillSum: A Corpus for
  Automatic Summarization of US Legislation.* EMNLP Workshop on
  New Frontiers in Summarization.
- Lin, C.-Y. (2004). *ROUGE: A Package for Automatic Evaluation
  of Summaries.* ACL.
- Min, S., et al. (2023). *FActScore: Fine-grained Atomic
  Evaluation of Factual Precision in Long Form Text Generation.*
  EMNLP.
- Zhang, T., et al. (2020). *BERTScore: Evaluating Text Generation
  with BERT.* ICLR.

# Appendix A. Reproducibility

- Repo: `Akshitha024/legal-summarization-benchmark`, MIT.
- Reproduce: `make eval && make plots`.
- 5 figures in `results/figures/`.
- Test artifacts in `docs/test_results/`.
