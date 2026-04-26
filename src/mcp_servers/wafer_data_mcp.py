"""wafer-data-mcp — MOCK MCP server for wafer process history.

In production, this is replaced by a real MCP server that queries the fab's
internal MES / yield system. For POC it reads from local CSVs in
$MOCK_FAB_DATA_DIR.

Tools:
    list_lots()
    get_defect_summary(wafer_ids?)
    download_wafer_history(wafer_ids?, stage_name_substr?, factor_types?)

All return JSON-serializable dicts (records orientation), so OpenCode can
inspect them as plain data.

Run:
    uv run wafer-data-mcp
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("MOCK_FAB_DATA_DIR", "./data/mock-fab-data")).resolve()
WAFER_HISTORY_CSV = DATA_DIR / "wafer_history.csv"
DEFECT_COUNTS_CSV = DATA_DIR / "defect_counts.csv"

mcp = FastMCP("wafer-data-mcp")


def _read_history() -> pd.DataFrame:
    if not WAFER_HISTORY_CSV.exists():
        raise FileNotFoundError(
            f"{WAFER_HISTORY_CSV} not found. Run "
            "`uv run python data/mock-fab-data/generate.py` first."
        )
    return pd.read_csv(WAFER_HISTORY_CSV)


def _read_defects() -> pd.DataFrame:
    if not DEFECT_COUNTS_CSV.exists():
        raise FileNotFoundError(f"{DEFECT_COUNTS_CSV} not found.")
    return pd.read_csv(DEFECT_COUNTS_CSV)


@mcp.tool()
async def list_lots() -> dict[str, Any]:
    """List the wafer IDs and lot IDs available in the mock fab data."""
    h = _read_history()
    wafers = sorted(h["wafer_id"].unique().tolist())
    lots = sorted(h["lot_id"].unique().tolist()) if "lot_id" in h.columns else []
    return {"wafer_ids": wafers, "lot_ids": lots, "n_wafers": len(wafers)}


@mcp.tool()
async def get_defect_summary(
    wafer_ids: list[str] | None = None,
    defect_type: str | None = None,
) -> dict[str, Any]:
    """Return per-wafer defect counts. If wafer_ids is None, returns all wafers.

    Each row: {wafer_id, defect_type, defect_count, scan_stage}
    """
    df = _read_defects()
    if wafer_ids:
        df = df[df["wafer_id"].isin(wafer_ids)]
    if defect_type:
        df = df[df["defect_type"] == defect_type]
    return {
        "rows": df.to_dict(orient="records"),
        "n_rows": len(df),
        "columns": list(df.columns),
    }


@mcp.tool()
async def download_wafer_history(
    wafer_ids: list[str] | None = None,
    stage_name_substr: str | None = None,
    factor_types: list[str] | None = None,
    drop_dummy_steps: bool = False,
) -> dict[str, Any]:
    """Return wafer process history.

    Args:
        wafer_ids: optional filter
        stage_name_substr: optional substring filter on process_name
            (e.g. "VIA_ETCH" matches "M2_VIA_ETCH")
        factor_types: optional list of column names to include
            (default: all). Always includes wafer_id + process_step.
        drop_dummy_steps: if True, drops steps whose name contains "DUMMY"
            or "SCRIBE" or starts with "_".
    """
    df = _read_history()
    if wafer_ids:
        df = df[df["wafer_id"].isin(wafer_ids)]
    if stage_name_substr:
        df = df[df["process_name"].str.contains(stage_name_substr, case=False, na=False)]
    if drop_dummy_steps:
        mask = ~df["process_name"].str.contains("DUMMY|SCRIBE", case=False, na=False)
        df = df[mask]
    if factor_types:
        keep = ["wafer_id", "process_name", "step_id"]
        keep += [c for c in factor_types if c in df.columns]
        df = df[[c for c in keep if c in df.columns]]
    return {
        "rows": df.to_dict(orient="records"),
        "n_rows": len(df),
        "columns": list(df.columns),
    }


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    mcp.run()


if __name__ == "__main__":
    main()
