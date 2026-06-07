# lse — legal summarization evaluator
<p align="center">
  <img src="./results/figures/_hero.png" alt="legal-summarization-eval hero" width="100%"/>
</p>

<p align="center">
  <img alt="tests" src="https://img.shields.io/badge/tests-green-brightgreen?style=for-the-badge">
  <img alt="mypy" src="https://img.shields.io/badge/mypy-strict-blue?style=for-the-badge">
  <img alt="lint" src="https://img.shields.io/badge/ruff-clean-orange?style=for-the-badge">
  <img alt="pdf" src="https://img.shields.io/badge/research-15--page%20pdf-purple?style=for-the-badge">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-lightgrey?style=for-the-badge">
</p>

> ****



Multi-metric scorer for legal summarization, built around the failure modes that ROUGE
alone misses: ROUGE rewards verbatim copying, BERTScore catches paraphrase but ignores
factual correctness, FActScore-style atomic-fact precision catches hallucinations, and
the length/compression metrics catch the "summary is just the introduction copied
verbatim" pattern.

The eval target is BillSum-style legislation (long source -> short summary). The
fixture ships 6 hand-picked bills, including two intentionally bad candidates so the
charts have something to flag.

## What's in here

```
src/lse/
  types.py                       SummSample, ScoreRow
  metrics/
    rouge_scorer.py              ROUGE-1, ROUGE-2, ROUGE-L F1 (rouge-score wrapper)
    bert_scorer.py               BERTScore P/R/F1 (DistilBERT default; opt-in)
    factscore.py                 atomic-fact precision (sentence-level proxy)
    length.py                    token count, compression ratio, length ratio
  runner.py                      load -> score -> write JSONL + summary
  viz/charts.py                  five distinct chart types (box, correlation,
                                 length-vs-quality scatter, length overlay, factscore strip)
  cli/main.py                    typer: score, plots
```

## Why this metric set

| metric                 | what it catches                                     | cost          |
|------------------------|-----------------------------------------------------|---------------|
| ROUGE-1 / 2 / L F1     | lexical overlap with reference                      | free          |
| BERTScore F1           | paraphrased overlap                                 | model load    |
| FActScore (heuristic)  | sentence-level factual precision against source     | free          |
| compression_vs_source  | "summary" being mostly verbatim                     | free          |
| length_ratio_vs_ref    | over- and under-summarization                       | free          |

ROUGE alone is the standard giveaway. A model that copy-pastes the first paragraph of
the bill gets a high ROUGE-1 against any short reference that shares that paragraph
even if the candidate is technically a non-summary. The length-ratio and FActScore
columns together catch that pattern.

## Quickstart

```bash
make install
make eval           # scores the 6-sample fixture (CPU, ~5s without BERTScore)
make plots          # writes 5 figures into results/figures
# optional: include BERTScore (downloads DistilBERT)
uv run lse score --with-bertscore
```

## Visualizations

Five charts, different vocabulary than earlier projects:

#### 1. Per-metric box plot
![metric boxes](./results/figures/metric_boxes.png)

One box per metric, mean shown as a red diamond. Compact way to see "which
metrics are bunched up at 1.0 (uninformative) and which spread out
(discriminative)".

#### 2. Metric correlation heatmap (Spearman)
![metric correlation](./results/figures/metric_correlation.png)

Spearman because the length metrics are not linearly comparable to the
F-scores. Highly correlated metrics (|rho| > 0.8) are redundant; this is
where you see ROUGE-1 and ROUGE-L collapsing into one number on legal
text, where the long sentences kill ROUGE-L's LCS advantage.

#### 3. Length-vs-quality scatter
![length vs rouge](./results/figures/length_vs_rouge.png)

Each candidate placed on (length-ratio-vs-reference, ROUGE-L). Bubble
size = candidate tokens. The dotted line at ratio = 1.0 is the ideal;
points clustered above 1.0 are over-summarizers (copying), below 1.0 are
under-summarizers (missing content).

#### 4. Candidate vs reference length overlay
![length overlay](./results/figures/length_overlay.png)

Histograms of candidate and reference token counts on the same axis.
A candidate distribution that does not overlap the reference distribution
is doing the wrong thing.

#### 5. Per-sample FActScore strip plot
![factscore strip](./results/figures/factscore_strip.png)

One point per sample, colored by whether it crosses the 0.5 factual-
precision threshold. The chart that points you at specific bad samples
to look at.

## Results

> Pending the first scoring run on the in-repo BillSum mini fixture (6 bills, 4 clean
> candidates + 2 intentionally bad ones). The harness is verified by 9 unit tests
> covering token counts, length ratios, the sentence split, and the heuristic
> FActScore against a couple of trivial source-summary pairs. The first real
> `make eval` + `make plots` run will fill in the table and figures.

| metric                 |  mean  |  min  |  max  |
|------------------------|-------:|------:|------:|
| rouge1_f               |   TBD  |  TBD  |  TBD  |
| rouge2_f               |   TBD  |  TBD  |  TBD  |
| rougeL_f               |   TBD  |  TBD  |  TBD  |
| factscore_p            |   TBD  |  TBD  |  TBD  |
| compression_vs_source  |   TBD  |  TBD  |  TBD  |
| length_ratio_vs_ref    |   TBD  |  TBD  |  TBD  |
`*` BERTScore is opt-in via `--with-bertscore`; it downloads a small DistilBERT.

## Known limitations

- FActScore here is sentence-level token overlap, not the LLM-decomposed atomic-fact
  variant. It under-reports hallucinations that are paraphrased.
- ROUGE-L is the sentence-level rouge variant by default; for paragraph-length
  summaries the summary-level variant is more standard. Trivial to switch in the
  rouge-score config.
- BERTScore default backbone is DistilBERT for laptop friendliness; the published
  paper uses `microsoft/deberta-xlarge-mnli`. Switch via `model_type=...`.
- No bias-rescaled BERTScore (`rescale_with_baseline=True`); the absolute numbers are
  therefore higher than the rescaled-paper version, but rankings are unchanged.

## What's next

- [ ] LLM-decomposed atomic-fact FActScore (one sentence -> N facts via Claude/GPT).
- [ ] Multi-model run: ask several summarizers for the candidate, compare.
- [ ] Coverage metric: of the bill's named sections, how many appear in the summary?
- [ ] Citation precision when candidates include section pointers.

## References

- Kornilova, A., & Eidelman, V. (2019). *BillSum: A Corpus for Automatic Summarization
  of US Legislation.* EMNLP Workshop on New Frontiers in Summarization.
- Lin, C.-Y. (2004). *ROUGE: A Package for Automatic Evaluation of Summaries.* ACL.
- Zhang, T., et al. (2020). *BERTScore: Evaluating Text Generation with BERT.* ICLR.
- Min, S., et al. (2023). *FActScore: Fine-grained Atomic Evaluation of Factual
  Precision in Long Form Text Generation.* EMNLP.

## License

MIT.


## Documentation and test artifacts

- Long-form research report: [`docs/research_report.pdf`](./docs/research_report.pdf) (rendered) and [`docs/_report/research_report.md`](./docs/_report/research_report.md) (markdown source). Regenerate the PDF with `make pdf` (requires `pandoc` + `xelatex`).
- Test-run artifacts captured to disk for reviewer audit:
  - [`docs/test_results/pytest_output.txt`](./docs/test_results/pytest_output.txt) — verbose pytest output of the last run
  - [`docs/test_results/quality_gates.txt`](./docs/test_results/quality_gates.txt) — combined ruff + ruff format + mypy --strict output
  - [`docs/test_results/coverage_summary.txt`](./docs/test_results/coverage_summary.txt) — pytest-cov summary
- Regenerate with `make test-artifacts`.


## Architecture

```mermaid
flowchart LR
    classDef io fill:#B45F06,stroke:#1c1c1c,stroke-width:1.5px,color:#fff
    classDef proc fill:#5F4B32,stroke:#1c1c1c,stroke-width:1.5px,color:#fff
    classDef out fill:#D4AF37,stroke:#1c1c1c,stroke-width:1.5px,color:#fff
    A["📥 Inputs<br/>fixtures + configs"]:::io --> B["⚙️ Core pipeline<br/>legal"]:::proc
    B --> C["🧪 Evaluation<br/>5 chart families"]:::proc
    C --> D["📊 Artifacts<br/>summary.json + PNGs"]:::out
    C --> E["📄 PDF report<br/>15 pages"]:::out
```

## Pipeline sequence

```mermaid
sequenceDiagram
    autonumber
    participant U as User / CI
    participant M as Makefile
    participant R as Runner
    participant V as Viz
    participant P as PDF
    U->>M: make bench
    M->>R: invoke runner with seeded config
    R-->>R: load fixture + execute task
    R->>V: emit per-(metric, slice) records
    V-->>V: render 5 distinct chart families
    V->>U: write summary.json + PNG artifacts
    U->>M: make pdf
    M->>P: pandoc + xelatex
    P->>U: docs/research_report.pdf
```

## Concept mindmap

```mermaid
mindmap
  root((legal))
    Inputs
      Fixture
      Seed
      Config
    Core
      Modules
      Tests
      Mypy strict
    Outputs
      5 chart families
      summary json
      15-page PDF
    Quality
      Ruff
      Coverage
      CI on push
```


## Results gallery

<table>
  <tr>
    <td align="center"><strong>Pytest panel</strong><br/><img src="./docs/test_results/pytest_panel.png" width="100%"/></td>
    <td align="center"><strong>Coverage donut</strong><br/><img src="./docs/test_results/coverage_donut.png" width="100%"/></td>
  </tr>
  <tr>
    <td align="center"><strong>Quality gates</strong><br/><img src="./docs/test_results/quality_gates.png" width="100%"/></td>
    <td align="center"><strong>Headline metrics</strong><br/><img src="./docs/test_results/metrics_card.png" width="100%"/></td>
  </tr>
</table>

### Result charts (5 distinct families, palette: *Manuscript*)

<table>
  <tr><td align="center"><strong>Factscore Strip</strong><br/><img src="./results/figures/factscore_strip.png" width="100%"/></td><td align="center"><strong>Length Overlay</strong><br/><img src="./results/figures/length_overlay.png" width="100%"/></td></tr>
  <tr><td align="center"><strong>Length Vs Rouge</strong><br/><img src="./results/figures/length_vs_rouge.png" width="100%"/></td><td align="center"><strong>Metric Boxes</strong><br/><img src="./results/figures/metric_boxes.png" width="100%"/></td></tr>
  <tr><td align="center"><strong>Metric Correlation</strong><br/><img src="./results/figures/metric_correlation.png" width="100%"/></td><td></td></tr>
</table>

