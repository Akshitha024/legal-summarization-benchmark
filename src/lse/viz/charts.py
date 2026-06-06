"""Five distinct charts for summarization eval.

Different from prior project sets again: a metric-correlation matrix, a
length-vs-quality scatter, a per-metric box plot, a length-distribution
overlay (candidate vs reference), and an outlier-flagging strip plot.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _metric_keys(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    return sorted(k for k in rows[0] if isinstance(rows[0][k], int | float) and k != "sid")


# 1. Box plot of every metric (one box per metric)
def plot_metric_boxes(scores_path: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(scores_path)
    keys = [k for k in _metric_keys(rows) if any(0 <= r[k] <= 1.5 for r in rows)]
    if not keys:
        out.write_bytes(b"")
        return out
    data = [[float(r[k]) for r in rows if k in r] for k in keys]
    fig, ax = plt.subplots(figsize=(max(6, 0.8 * len(keys) + 2), 5))
    bplot = ax.boxplot(
        data,
        tick_labels=keys,
        patch_artist=True,
        showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "red", "markeredgecolor": "red"},
    )
    for patch in bplot["boxes"]:
        patch.set_facecolor("#aec7e8")
        patch.set_alpha(0.7)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
    ax.set_ylim(-0.05, 1.2)
    ax.set_ylabel("score")
    ax.set_title("Per-metric distribution (red diamond = mean)")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# 2. Metric correlation heatmap (Spearman, not Pearson, to handle the non-
#    linear length metrics gracefully)
def plot_metric_correlation(scores_path: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(scores_path)
    keys = _metric_keys(rows)
    if len(keys) < 2:
        out.write_bytes(b"")
        return out
    from scipy.stats import spearmanr

    mat = np.array([[float(r.get(k, 0)) for k in keys] for r in rows], dtype=np.float64)
    if mat.std() == 0:
        out.write_bytes(b"")
        return out
    corr, _ = spearmanr(mat, axis=0)
    if np.ndim(corr) == 0:
        corr = np.array([[1.0]])
    fig, ax = plt.subplots(figsize=(max(6, 0.6 * len(keys)), max(5, 0.5 * len(keys))))
    im = ax.imshow(corr, cmap="PuOr_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels(keys, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels(keys, fontsize=8)
    for i in range(len(keys)):
        for j in range(len(keys)):
            ax.text(
                j,
                i,
                f"{corr[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=7,
                color="white" if abs(corr[i, j]) > 0.5 else "black",
            )
    fig.colorbar(im, ax=ax, label="Spearman rho")
    ax.set_title("Metric correlation (Spearman)")
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# 3. Length-vs-quality scatter
def plot_length_vs_rouge(scores_path: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(scores_path)
    if not rows:
        out.write_bytes(b"")
        return out
    xs = [r.get("length_ratio_vs_ref", 0) for r in rows]
    ys = [r.get("rougeL_f", 0) for r in rows]
    sizes = [50 + 0.5 * r.get("cand_tokens", 0) for r in rows]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(xs, ys, s=sizes, alpha=0.6, edgecolor="black")
    ax.axvline(1.0, color="gray", linestyle=":", linewidth=1, label="ideal ratio = 1.0")
    ax.set_xlabel("candidate length / reference length")
    ax.set_ylabel("ROUGE-L F1")
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)
    ax.set_title("Length ratio vs. ROUGE-L (bubble size = candidate tokens)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# 4. Candidate vs reference length histograms overlay
def plot_length_overlay(scores_path: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(scores_path)
    if not rows:
        out.write_bytes(b"")
        return out
    cand = [r.get("cand_tokens", 0) for r in rows]
    ref = [r.get("ref_tokens", 0) for r in rows]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    bins = 12
    ax.hist(cand, bins=bins, alpha=0.5, label="candidate", color="#1f77b4", edgecolor="black")
    ax.hist(ref, bins=bins, alpha=0.5, label="reference", color="#ff7f0e", edgecolor="black")
    ax.set_xlabel("tokens")
    ax.set_ylabel("count")
    ax.set_title("Candidate vs. reference length distribution")
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# 5. Per-sample factscore_p strip plot, highlighting outliers
def plot_factscore_strip(scores_path: Path, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(scores_path)
    if not rows:
        out.write_bytes(b"")
        return out
    vals = [r.get("factscore_p", 0) for r in rows]
    sids = [r.get("sid", str(i)) for i, r in enumerate(rows)]
    threshold = 0.5
    colors = ["#d62728" if v < threshold else "#2ca02c" for v in vals]
    fig, ax = plt.subplots(figsize=(max(6, 0.4 * len(rows) + 3), 4.5))
    ax.scatter(range(len(rows)), vals, c=colors, s=120, edgecolor="black")
    ax.axhline(
        threshold, color="gray", linestyle=":", linewidth=1, label=f"threshold = {threshold}"
    )
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(sids, rotation=30, ha="right", fontsize=8)
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("FActScore (atomic-fact precision)")
    ax.set_title("Per-sample factual precision (red = below threshold)")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out
