# RCA Report — DRAFT

## Correlation observed

(What statistical correlation triggered this RCA? wafer/lot/defect_count data,
score from stats algo, etc.)

## Mechanisms (causal pathways considered)

(For each candidate factor: physical / chemical mechanism that could plausibly
drive A → B. Cite KB snippets where possible.)

## Confounders

(Common-cause variables that could produce the correlation without A causing B.)

## Verdict

(plausible / uncertain / implausible — with reasoning.)

## Suggested investigations

(DOE knobs, splits, monitor measurements to confirm or refute.)

## Knowledge gaps

(Things the KB couldn't answer; flagged for future ingestion.)

---

*This is a draft. Once you and the agent agree on the wording, click "Submit
final" in the web UI to create the final RCAReport (with `agreed=True`).
Manager signoff happens separately via `/sign` on the backend.*
