# Sequential EDA session protocol

Each **session** is a short, pre-registered test package (typically 3–4 stages, 4–6 argued figures). It does not replace Stages 1–14; it builds on their artefacts under `eda/outputs/impact_eda/`.

## Before running

1. Write `SESSION_{X}_HYPOTHESES.md` with claims, tests, data/grain, and **falsifiers** before any code executes.
2. Implement stages in a dedicated runner (e.g. `python -m eda.impact_session_a --through 18`).
3. Write `STAGE{N}_GATE.md` per stage with outputs and the command to reproduce.

## Figures

- Notebook: `session_{x}_figures.ipynb` → `outputs/impact_eda/figures/session_{x}/`.
- One clear claim per figure; annotated like Stage 9 (not generic bar charts).
- Maximum **6** figures per session.
- Do not duplicate `figures/stage9/` or `figures/stage10_14/` without a new analytical angle.

## After the last stage — close-out

Write `SESSION_{X}_CLOSEOUT.md` with **exactly** these sections:

### 1. What was tested

Hypotheses, grain (county-year, county-month, etc.), and **n at each join** (no silent row loss).

### 2. Outcomes

For each hypothesis: **supported / tentative / falsified / broken test**. One paragraph each; no new claims beyond what the tables support.

### 3. Issues remaining

Artefacts, power limits, join loss, product breaks. These become the first work item of the next session.

### 4. Branch decision

Per trajectory (e.g. crop exposure, hydro lead-time, conflict seasonality): **KEEP / CUT / PIVOT**, citing the pre-declared kill criterion.

### 5. External data ask

At most **3** datasets. For each:

| Field | Content |
|-------|---------|
| Dataset | Name and typical host (HDX, FEWS, Copernicus, etc.) |
| Grain | Spatial and temporal resolution needed |
| Gap | Why current course-pack / `data/` cannot answer the question |
| Unblocks | What claim or deliverable it would enable |
| Search prompt | Paste-ready query for the user |

### 6. Next-session prompt

A copy-paste block for a new Cursor chat:

- Session goals and stage numbers
- Files to read first (`SESSION_*_CLOSEOUT.md`, gate CSVs, hypotheses)
- Tests **not** to reopen (lock-ins from prior sessions)
- Expected figures and deliverables

## Redundancy and discipline (carry forward)

- OCHA: one snapshot per validation task (e.g. 20251130); never stack snapshots.
- GED: type-2 **or** Non-State as one conflict channel, not both as independent predictors.
- DTM `*_disaster` is an **outcome**, not a flood hazard label.
- ASAP crop/rangeland ≠ FEWS harvested area (exposure vs annual outcome).
- Stage 8 `go_no_go.csv`: combined crop+conflict model stays **no_go** until branches survive independently.

## README pointer

Update [`IMPACT_EDA_README.md`](IMPACT_EDA_README.md) with each new session row (command, hypotheses file, close-out, figures).
