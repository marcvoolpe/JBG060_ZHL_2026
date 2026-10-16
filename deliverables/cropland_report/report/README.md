# Methodological report (LaTeX)

Two versions of the same story (rewritten 15 Oct for readability), same template, numbers, figures and references:

| file | what it is |
|---|---|
| `report_draft.tex` | **the long version**: the whole story with every detail, about 6,300 words with captions in the main text, plus appendices A-J (35 pages). Results waiting for a group decision carry an orange `[pending decision N]` tag (REVIEW_PLAN.md, section 4); red `[...]` marks what is still to write. Change the story here first. |
| `report_final.tex` | **the version to submit, within 2,000 words**: the same story and order, cut to the essentials, with 4 figures and 2 tables (7 pages). Draft marks are switched off (`\draftfalse`), so it shows the group's proposals for the pending decisions. Before submitting: full names and student numbers in the author line. |
| `report_draft.md`, `report_final.md` | **reading copies for GitHub**, numbers filled in, figures shown. Generated: do not edit them; run `python deliverables/cropland_report/report/draft_to_markdown.py` (long) and `... draft_to_markdown.py report_final` (final). |
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

**Since 14 Oct the shared Overleaf project is the master copy of the text.** It is synced to a local folder with the VS Code extension Overleaf Workshop (Local Replica). To refresh numbers or tables without losing anyone's edits, always go in this order:
1. copy the Overleaf `report_draft.tex` (from the replica folder, or Overleaf > Menu > Download source) over `report/report_draft.tex` in the repo;
2. run `build_report_inputs.py` (it rewrites only the `%% <<...>>` blocks);
3. copy `report_draft.tex` (and any new figure) back into the replica folder; the extension uploads it.
Never copy the repo file to Overleaf without step 1: it would overwrite the group's edits.

## Word limit (2,000 words, captions included, words in tables and figures not)

- On 15 Oct the final version had **1,951 words** counted the way Overleaf does (about 1,990 if every citation is counted as the words it prints). Keep it under 2,000 after every edit.
- Overleaf: Menu > Word Count. Table bodies are wrapped in `%TC:ignore ... %TC:endignore`, and `\ph`, `\idea`, `\pending` are ignored by the counter. Add "words in headers" and "words in floats/captions" to the count.
- Whether appendices count is set on Canvas; the final version has none, so it stands on its own either way.

## How the text is written (15 Oct, from report_readability_plan.md and Mensh and Kording 2017)

- One message: the map, not the flood, decides whether a trigger fires; a labelled sample measures cropland honestly and shows which map to trust.
- One arc: Context (and: floods, ZOA's trigger) -> but (the maps disagree, nobody checked them) -> therefore (we measure, score, and follow the answer to the trigger). Each section opens by linking to the one before and ends by handing over to the next.
- Results follow the four sub-objectives, each paragraph headed by its finding, then the number, then at most one caveat. The Discussion answers the sub-objectives in the same order; all other caveats sit in one Limits paragraph.
- Plain words and "we": missed fields, false alarms, boxes the labellers saw as empty. Captions say what the figure shows, never how the review went.

## Compiled and checked (14 Oct)

Both files compile without errors, overfull lines or undefined references (Tectonic 0.15, a self-contained LaTeX engine: `tectonic report_draft.tex` in a copy of this folder with `figures/`). Fixed on 14 Oct: the data table (its first column did not wrap and pushed the others off the page), an underscore in the skeleton, the author line, and the float placement (figures now sit next to their text instead of after the references). The draft is 12 pages. Overleaf (pdfLaTeX + BibTeX) should give the same result.
