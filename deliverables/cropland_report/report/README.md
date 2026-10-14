# Methodological report (LaTeX)

Two versions, same template, same figures and references:

| file | what it is |
|---|---|
| `report_draft.tex` | **the full draft written from our results (14 Oct)**: about 5,000 words with captions in the main text plus an appendix A-G (all 26 figures and 11 tables, 31 pages), so the group cuts rather than writes. Results waiting for a group decision carry an orange `[pending decision N]` tag (REVIEW_PLAN.md, section 4); red `[...]` marks what is still to write or make (names, the method diagram); blue "Idea" boxes suggest what to cut. |
| `report_draft.md` | **a reading copy of the draft for GitHub**, with the numbers filled in, the figures shown and a reference list. Generated: do not edit it; edit `report_draft.tex` and run `python deliverables/cropland_report/report/draft_to_markdown.py`. |
| `report.tex` | the earlier skeleton: the eight rubric headings with placeholders, idea boxes and a word target per section. Kept for its notes; the draft supersedes it. |

The long notes behind each section are in `deliverables/cropland_report/notes/` (01-08); the results with every number are in notes 07, section 7.0.

## Read and edit it on Overleaf

`report_draft.tex` is **self-contained**: every number, the appendix tables and the reference list are inside the file. Only the images are separate.

1. Overleaf > New project > **Upload project** > `overleaf_upload.zip` (in this folder, made by the build script: `report_draft.tex` + `figures/`).
   Or: New project > Blank project, delete `main.tex`, upload `report_draft.tex` and drag in the folder `deliverables/cropland_report/figures/` as `figures`.
2. Compile (pdfLaTeX, the default). Without the `figures/` folder it still compiles; each figure shows as a grey box naming the figure.

## Numbers are never typed by hand

`python deliverables/cropland_report/report/build_report_inputs.py` reads the CSVs and rewrites the blocks inside `report_draft.tex` between lines like `%% <<numbers>> ...` and `%% <</numbers>>` (numbers, the four appendix tables, the bibliography). **Do not edit between those lines**: edit the CSV or the script, then rebuild. Everything outside the blocks is ordinary text to edit. It also writes:
- `numbers.tex` and `results.tex` (the same macros, used by the skeleton `report.tex` and the Markdown copy), e.g. `\AwAreaHa` = 116,500, `\RuleOneFone` = 0.72;
- `app_sample.tex`, `app_models.tex`, `app_accuracy.tex`, `app_floods.tex` (the appendix tables, also embedded in the draft);
- `figures/` (copies of all figures, not in git) and `overleaf_upload.zip`.

Edits made on Overleaf live only on Overleaf: copy the file back into the repo to keep them. A rebuild rewrites only the generated blocks, never the text around them.

## Word limit (2,000 words, captions included, words in tables and figures not)

- Switch `\drafttrue` to `\draftfalse`: tags, placeholders and idea boxes disappear.
- Overleaf: Menu > Word Count. Table bodies are wrapped in `%TC:ignore ... %TC:endignore`, and `\ph`, `\idea`, `\pending` are ignored by the counter. Add "words in headers" and "words in floats/captions" to the count.
- The draft is about twice the limit. The idea box under Results suggests which figures to move to the poster; the Discussion and Approach have the most room to cut.

## Compiled and checked (14 Oct)

Both files compile without errors, overfull lines or undefined references (Tectonic 0.15, a self-contained LaTeX engine: `tectonic report_draft.tex` in a copy of this folder with `figures/`). Fixed on 14 Oct: the data table (its first column did not wrap and pushed the others off the page), an underscore in the skeleton, the author line, and the float placement (figures now sit next to their text instead of after the references). The draft is 12 pages. Overleaf (pdfLaTeX + BibTeX) should give the same result.
