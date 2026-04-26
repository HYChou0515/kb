# Mock fab data

POC stand-in for a real wafer process history + defect count export.

## Files

- `generate.py` — deterministic generator (seed=42). Writes the two CSVs below.
- `wafer_history.csv` — long format, one row per (wafer_id, step). Columns:
  `wafer_id, lot_id, step_id, process_name, tool_id, timestamp`.
- `defect_counts.csv` — per-wafer defect counts. Columns:
  `wafer_id, defect_type, defect_count, scan_stage`.

## How to (re)generate

```bash
uv run python data/mock-fab-data/generate.py
```

## Story baked into the data

- **50 wafers**, 5 lots × 10 wafers each.
- **20 process steps**, including 2 dummy steps (`DUMMY_PRE_QC`, `SCRIBE_INSPECT`)
  that the user is expected to drop in step 6 of the RCA flow.
- **True root cause:** at step `M2_VIA_ETCH`, tool `ETCH_C` causes a stuck-particle
  problem. Wafers passing through `ETCH_C` at this step show ~3× the defect count.
- **Many spurious correlations** show up because of small N + many factors —
  exactly the failure mode the KG filter is meant to fix.

The agent in OpenCode should walk the user through the steps, end up running
the stats algo, and then use the KB to drop spurious factors and surface
`M2_VIA_ETCH × ETCH_C` as the only candidate with a plausible mechanism
(particle contamination during via etch → metal short on M2).
