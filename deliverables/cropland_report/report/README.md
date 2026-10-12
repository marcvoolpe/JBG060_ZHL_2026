# Methodological report (LaTeX skeleton)

`report.tex` has the eight rubric headings, draft text where we already have content, red `[placeholders]` for what is still to come, blue "Idea" boxes with choices to make, and a word target per section. The long notes behind each section are in `deliverables/cropland_report/notes/` (01-08).

## Build and upload

1. Run `cropland/eda_public_maps.ipynb` (writes `deliverables/cropland_report/tables/key_numbers.csv` and the figures).
2. `python deliverables/cropland_report/report/build_report_inputs.py` writes:
   - `numbers.tex`: one LaTeX macro per quoted number (e.g. `\AwCropMin` = 0.22\%). Never type a result by hand: rerun the notebook and this script, and the report follows;
   - `figures/`: the notebook's figures (PNG, not in git);
   - `overleaf_upload.zip`: everything Overleaf needs. Overleaf: New project > Upload project > the zip.
3. Compile with pdfLaTeX + BibTeX (Overleaf does this by default).

## Word limit (2,000 words, captions included, words in tables and figures not)

- Switch `\drafttrue` to `\draftfalse` in `report.tex`: placeholders, idea boxes and word targets disappear.
- Overleaf: Menu > Word Count. Table bodies are wrapped in `%TC:ignore ... %TC:endignore`, and `\ph`, `\idea`, `\budget` are ignored by the counter, so Overleaf's count follows the course rule. Add "words in headers" and "words in floats/captions" to the text count.

## Not checked locally

There is no LaTeX on the laptop where this was written; the file was checked for balanced environments, braces, labels and citations only (`check_tex.py`, in the agent's scratchpad). Compile once on Overleaf and fix anything it reports.
