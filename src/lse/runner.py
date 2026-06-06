"""Orchestrator: score a JSONL of (source, reference, candidate) samples."""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger
from tqdm import tqdm

from .metrics.factscore import factscore_heuristic
from .metrics.length import length_stats
from .metrics.rouge_scorer import rouge
from .types import ScoreRow, SummSample


def load_jsonl(path: Path) -> list[SummSample]:
    out: list[SummSample] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            out.append(
                SummSample(
                    sid=str(o["sid"]),
                    source=str(o["source"]),
                    reference=str(o["reference"]),
                    candidate=str(o["candidate"]),
                    cited_sources=tuple(o.get("cited_sources", [])),
                )
            )
    logger.info("loaded {} samples", len(out))
    return out


def score(
    samples: list[SummSample],
    with_bertscore: bool = False,
) -> list[ScoreRow]:
    """Score every sample on all cheap metrics. BERTScore is opt-in because
    it loads a model.
    """
    rows: list[ScoreRow] = []
    cands: list[str] = []
    refs: list[str] = []
    for s in tqdm(samples, desc="rouge+factscore+length"):
        r = ScoreRow(sid=s.sid)
        r.metrics.update(rouge(s.candidate, s.reference))
        r.metrics.update(factscore_heuristic(s.candidate, s.source))
        r.metrics.update(length_stats(s.candidate, s.reference, s.source))
        r.candidate_len_tokens = int(r.metrics["cand_tokens"])
        r.reference_len_tokens = int(r.metrics["ref_tokens"])
        rows.append(r)
        cands.append(s.candidate)
        refs.append(s.reference)

    if with_bertscore:
        try:
            from .metrics.bert_scorer import bert_score_batch

            bs = bert_score_batch(cands, refs)
            for r, b in zip(rows, bs, strict=True):
                r.metrics.update(b)
        except Exception as e:
            logger.warning("BERTScore failed: {} (skipping)", e)
    return rows


def write(out_dir: Path, run_id: str, rows: list[ScoreRow]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{run_id}__scores.jsonl"
    with p.open("w") as f:
        for r in rows:
            f.write(
                json.dumps(
                    {
                        "sid": r.sid,
                        **r.metrics,
                    }
                )
                + "\n"
            )
    summary: dict[str, float] = {}
    if rows:
        keys = sorted({k for r in rows for k in r.metrics})
        for k in keys:
            vals = [r.metrics[k] for r in rows if k in r.metrics]
            summary[k] = sum(vals) / len(vals)
    (out_dir / f"{run_id}__summary.json").write_text(
        json.dumps({"run_id": run_id, "n": len(rows), "means": summary}, indent=2)
    )
    return p
