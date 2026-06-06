from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger
from tabulate import tabulate

from ..runner import load_jsonl, score, write
from ..viz.charts import (
    plot_factscore_strip,
    plot_length_overlay,
    plot_length_vs_rouge,
    plot_metric_boxes,
    plot_metric_correlation,
)

app = typer.Typer(add_completion=False, help="lse: legal summarization evaluator")


@app.command("score")
def cmd_score(
    data: Annotated[Path, typer.Option(help="JSONL of (sid, source, reference, candidate)")] = Path(
        "tests/fixtures/billsum_mini.jsonl"
    ),
    out_dir: Annotated[Path, typer.Option(help="results dir")] = Path("results"),
    run_id: Annotated[str, typer.Option(help="run label")] = "latest",
    with_bertscore: Annotated[bool, typer.Option(help="include BERTScore (loads a model)")] = False,
) -> None:
    samples = load_jsonl(data)
    rows = score(samples, with_bertscore=with_bertscore)
    p = write(out_dir, run_id, rows)
    s = json.loads((out_dir / f"{run_id}__summary.json").read_text())
    table = [(k, v) for k, v in s["means"].items()]
    print()
    print(tabulate(table, headers=["metric", "mean"], floatfmt=".3f", tablefmt="github"))
    logger.info("wrote {}", p)


@app.command("plots")
def cmd_plots(
    scores: Annotated[Path, typer.Option(help="scores jsonl")] = Path(
        "results/latest__scores.jsonl"
    ),
    out_dir: Annotated[Path, typer.Option(help="figures dir")] = Path("results/figures"),
) -> None:
    plot_metric_boxes(scores, out_dir / "metric_boxes.png")
    plot_metric_correlation(scores, out_dir / "metric_correlation.png")
    plot_length_vs_rouge(scores, out_dir / "length_vs_rouge.png")
    plot_length_overlay(scores, out_dir / "length_overlay.png")
    plot_factscore_strip(scores, out_dir / "factscore_strip.png")
    typer.echo(f"wrote 5 figures to {out_dir}")


if __name__ == "__main__":
    app()
