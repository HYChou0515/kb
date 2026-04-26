"""Generate mock fab data for the RCA POC demo.

Writes:
    wafer_history.csv  — long format: (wafer_id, lot_id, step_id, process_name, tool_id, timestamp)
    defect_counts.csv  — (wafer_id, defect_type, defect_count, scan_stage)

Story baked in:
    - 50 wafers across 5 lots
    - 20 process steps including 2 "dummy" steps the user should drop
    - Each step has 3-5 candidate tools, wafers split unevenly across them
    - TRUE root cause:
        process step "M2_VIA_ETCH" has a stuck-particle issue on tool "ETCH_C"
        → wafers that went through ETCH_C at this step have ~3x defect count
    - Plus normal noise → many spurious correlations on small N (the whole
      point: stats algo over-generates false alarms; KG filter drops them).

Usage:
    uv run python data/mock-fab-data/generate.py
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent
SEED = 42

# ---- process flow definition ----------------------------------------------

PROCESS_FLOW: list[tuple[str, list[str]]] = [
    ("DUMMY_PRE_QC",       ["DUMMY_QC1", "DUMMY_QC2"]),
    ("DIFFUSION_PRECLEAN", ["WET_A", "WET_B", "WET_C"]),
    ("GATE_OXIDATION",     ["FURN_1", "FURN_2"]),
    ("POLY_DEPOSITION",    ["LPCVD_A", "LPCVD_B"]),
    ("POLY_LITHO",         ["SCAN_1", "SCAN_2", "SCAN_3"]),
    ("POLY_ETCH",          ["ETCH_P1", "ETCH_P2"]),
    ("SD_IMPLANT",         ["IMP_1", "IMP_2"]),
    ("SD_ANNEAL",          ["RTA_A", "RTA_B"]),
    ("ILD_DEPOSITION",     ["PECVD_A", "PECVD_B", "PECVD_C"]),
    ("M1_LITHO",           ["SCAN_1", "SCAN_2"]),
    ("M1_ETCH",            ["ETCH_M1", "ETCH_M2"]),
    ("M1_BARRIER_SEED",    ["PVD_A", "PVD_B"]),
    ("M1_PLATING",         ["PLT_1", "PLT_2"]),
    ("M1_CMP",             ["CMP_1", "CMP_2", "CMP_3"]),
    ("V1_DEPOSITION",      ["PECVD_A", "PECVD_B"]),
    ("V1_LITHO",           ["SCAN_1", "SCAN_3"]),
    ("M2_VIA_ETCH",        ["ETCH_A", "ETCH_B", "ETCH_C", "ETCH_D"]),
    ("M2_PLATING",         ["PLT_1", "PLT_2"]),
    ("M2_CMP",             ["CMP_1", "CMP_2"]),
    ("SCRIBE_INSPECT",     ["INSP_1"]),
]

LOTS = ["LOT_A", "LOT_B", "LOT_C", "LOT_D", "LOT_E"]
WAFERS_PER_LOT = 10
TRUE_CAUSE_STEP = "M2_VIA_ETCH"
TRUE_CAUSE_TOOL = "ETCH_C"
DEFECT_TYPE = "metal_short_M2"
SCAN_STAGE = "M2_CMP_POST"


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows_history: list[dict] = []
    wafer_paths: dict[str, dict[str, str]] = {}

    base_time = datetime(2026, 4, 1, 8, 0)
    for lot_idx, lot in enumerate(LOTS):
        for w_idx in range(WAFERS_PER_LOT):
            wafer_id = f"W{lot_idx*WAFERS_PER_LOT + w_idx + 1:03d}"
            wafer_paths[wafer_id] = {}
            t = base_time + timedelta(hours=lot_idx * 6 + w_idx * 0.1)
            for step_idx, (step_name, tools) in enumerate(PROCESS_FLOW):
                # Slight bias: tools picked roughly by lot, but with crossover
                tool = rng.choice(tools, p=_dist(len(tools), rng))
                wafer_paths[wafer_id][step_name] = str(tool)
                rows_history.append(
                    {
                        "wafer_id": wafer_id,
                        "lot_id": lot,
                        "step_id": f"S{step_idx+1:02d}",
                        "process_name": step_name,
                        "tool_id": str(tool),
                        "timestamp": (t + timedelta(minutes=step_idx * 30)).isoformat(timespec="seconds"),
                    }
                )

    history = pd.DataFrame(rows_history)

    # Defect count per wafer: baseline noise + bonus for hitting the true cause.
    defect_rows: list[dict] = []
    for wafer_id, path in wafer_paths.items():
        baseline = float(rng.normal(loc=20.0, scale=6.0))
        bonus = 50.0 if path.get(TRUE_CAUSE_STEP) == TRUE_CAUSE_TOOL else 0.0
        bonus += float(rng.normal(0, 4.0))
        defect_count = max(0, int(round(baseline + bonus)))
        defect_rows.append(
            {
                "wafer_id": wafer_id,
                "defect_type": DEFECT_TYPE,
                "defect_count": defect_count,
                "scan_stage": SCAN_STAGE,
            }
        )

    defects = pd.DataFrame(defect_rows)

    history.to_csv(OUT_DIR / "wafer_history.csv", index=False)
    defects.to_csv(OUT_DIR / "defect_counts.csv", index=False)

    print(f"Wrote {len(history)} history rows for {history['wafer_id'].nunique()} wafers.")
    print(f"Wrote {len(defects)} defect rows. Mean defects/wafer = {defects['defect_count'].mean():.1f}")
    print()
    print(f"True cause: tool {TRUE_CAUSE_TOOL} at step {TRUE_CAUSE_STEP}")
    cause_wafers = [w for w, p in wafer_paths.items() if p.get(TRUE_CAUSE_STEP) == TRUE_CAUSE_TOOL]
    print(f"  {len(cause_wafers)} wafer(s) went through it.")
    affected = defects.set_index("wafer_id").loc[cause_wafers, "defect_count"].mean()
    others = defects.set_index("wafer_id").drop(cause_wafers)["defect_count"].mean()
    print(f"  affected mean = {affected:.1f}, unaffected mean = {others:.1f}")


def _dist(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate an unequal probability distribution over n outcomes."""
    raw = rng.uniform(0.5, 2.0, size=n)
    return raw / raw.sum()


if __name__ == "__main__":
    main()
