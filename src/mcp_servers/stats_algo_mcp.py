"""stats-algo-mcp — MOCK MCP server simulating the in-house statistical scorer.

In production, replaced by an MCP wrapper around the real fab algorithm.
For POC, this implements a deliberately-noisy correlation scorer that
**over-generates false alarms** — exactly the failure mode the KG-backed
RCA filter is supposed to fix.

Algorithm (per (process_step, tool_id) candidate):
    1. Build a binary indicator: "wafer w went through tool t at step s".
    2. Compute Pearson r between that indicator and per-wafer defect_count.
    3. Bonus a small random "score noise" drawn from N(0, 0.1).
    4. Return all candidates with |r + noise| > threshold (default 0.25).

With ~50 wafers and ~80 (step, tool) pairs, you reliably get 10–30 false
alarms even when only one (step, tool) has a real signal.

Tools:
    compute_factor_scores(defect_type?, drop_dummy_steps?, threshold?)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("MOCK_FAB_DATA_DIR", "./data/mock-fab-data")).resolve()
WAFER_HISTORY_CSV = DATA_DIR / "wafer_history.csv"
DEFECT_COUNTS_CSV = DATA_DIR / "defect_counts.csv"
NOISE_SEED = int(os.getenv("STATS_NOISE_SEED", "1234"))

mcp = FastMCP("stats-algo-mcp")


def _build_indicator(history: pd.DataFrame) -> pd.DataFrame:
    """Wide-format indicator: rows=wafer_id, columns=(step|tool) pairs, values=0/1."""
    history = history.copy()
    history["factor_id"] = (
        history["process_name"].astype(str) + "::" + history["tool_id"].astype(str)
    )
    pivot = history.assign(value=1).pivot_table(
        index="wafer_id",
        columns="factor_id",
        values="value",
        aggfunc="max",
        fill_value=0,
    )
    return pivot


def _agg_defect_per_wafer(defects: pd.DataFrame, defect_type: str | None) -> pd.Series:
    if defect_type:
        defects = defects[defects["defect_type"] == defect_type]
    return defects.groupby("wafer_id")["defect_count"].sum()


@mcp.tool()
async def compute_factor_scores(
    defect_type: str | None = None,
    drop_dummy_steps: bool = True,
    threshold: float = 0.25,
    top_n: int = 50,
) -> dict[str, Any]:
    """Score every (process_step, tool_id) factor for correlation with
    per-wafer defect count. Deliberately noisy — many false alarms.

    Returns a list of candidates sorted by |score| descending:
        [{factor_id, process_step, tool_id, n_wafers, raw_pearson, score}, ...]

    The agent should NOT trust these scores blindly — that's the whole
    point of the KG-backed filter. Use `kb-mcp/recall_assessment` per
    candidate to drop the no-mechanism ones.
    """
    history = pd.read_csv(WAFER_HISTORY_CSV)
    defects = pd.read_csv(DEFECT_COUNTS_CSV)
    if drop_dummy_steps:
        mask = ~history["process_name"].str.contains(
            "DUMMY|SCRIBE", case=False, na=False
        )
        history = history[mask]

    indicator = _build_indicator(history)
    defect_per_wafer = _agg_defect_per_wafer(defects, defect_type)
    aligned = indicator.join(defect_per_wafer.rename("defect_count"), how="inner")
    if aligned.empty:
        return {"candidates": [], "n_wafers": 0, "n_factors": 0}

    rng = np.random.default_rng(NOISE_SEED)
    y = aligned["defect_count"].values.astype(float)
    y_centered = y - y.mean()
    y_norm = float(np.linalg.norm(y_centered)) or 1.0

    out: list[dict[str, Any]] = []
    for col in aligned.columns:
        if col == "defect_count":
            continue
        x = aligned[col].values.astype(float)
        if x.std() == 0:
            continue
        x_centered = x - x.mean()
        x_norm = float(np.linalg.norm(x_centered)) or 1.0
        r = float(np.dot(x_centered, y_centered) / (x_norm * y_norm))
        noise = float(rng.normal(0, 0.1))
        score = r + noise
        process_step, _, tool_id = col.partition("::")
        out.append(
            {
                "factor_id": col,
                "process_step": process_step,
                "tool_id": tool_id,
                "n_wafers_with_factor": int(x.sum()),
                "raw_pearson": round(r, 4),
                "score": round(score, 4),
            }
        )
    out = [c for c in out if abs(c["score"]) >= threshold]
    out.sort(key=lambda d: abs(d["score"]), reverse=True)
    return {
        "candidates": out[:top_n],
        "n_wafers": len(aligned),
        "n_factors": int(indicator.shape[1]),
        "threshold": threshold,
        "defect_type": defect_type,
    }


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    mcp.run()


if __name__ == "__main__":
    main()
