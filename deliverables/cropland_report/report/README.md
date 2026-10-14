# Methodological report (LaTeX)

Two versions, same template, same figures and references:

| file | what it is |
|---|---|
| `report_draft.tex` | **the full draft written from our results (14 Oct)**, about 4,100 words with captions, so the group cuts rather than writes. Results waiting for a group decision carry an orange `[pending decision N]` tag (REVIEW_PLAN.md, section 4); red `[...]` marks what is still to write or make (names, the method diagram); blue "Idea" boxes suggest what to cut. |
| `report_draft.md` | **a reading copy of the draft for GitHub**, with the numbers filled in, the figures shown and a reference list. Generated: do not edit it; edit `report_draft.tex` and run `python deliverables/cropland_report/report/draft_to_markdown.py`. |
| `report.tex` | the earlier skeleton: the eight rubric headings with placeholders, idea boxes and a word target per section. Kept for its notes; the draft supersedes it. |

The long notes behind each section are in `deliverables/cropland_report/notes/` (01-08); the results with every number are in notes 07, section 7.0.

## Numbers are never typed by hand

`python deliverables/cropland_report/report/build_report_inputs.py` writes:
- `numbers.tex`: the EDA numbers (from `tables/key_numbers.csv`, written by `cropland/eda_public_maps.ipynb`), e.g. `\AwCropMin` = 0.22\%;
- `results.tex`: the results (from `cropland/results/`, steps 09-12): area, F1, precision and recall of every map, flooded cropland, the 2000-2025 floods, e.g. `\AwAreaHa` = 116,500, `\RuleOneFone` = 0.72;
- `figures/`: copies of all figures (not in git);
- `overleaf_upload.zip`: both .tex files, references, numbers, results and figures. Overleaf: New project > Upload project > the zip, then compile `report_draft.tex`.

After any rerun of the pipeline, rerun the build script (and the Markdown converter): the text follows the new numbers.

## Word limit (2,000 words, captions included, words in tables and figures not)

- Switch `\drafttrue` to `\draftfalse`: tags, placeholders and idea boxes disappear.
- Overleaf: Menu > Word Count. Table bodies are wrapped in `%TC:ignore ... %TC:endignore`, and `\ph`, `\idea`, `\pending` are ignored by the counter. Add "words in headers" and "words in floats/captions" to the count.
- The draft is about twice the limit. The idea box under Results suggests which figures to move to the poster; the Discussion and Approach have the most room to cut.

## Compiled and checked (14 Oct)

Both files compile without errors, overfull lines or undefined references (Tectonic 0.15, a self-contained LaTeX engine: `tectonic report_draft.tex` in a copy of this folder with `figures/`). Fixed on 14 Oct: the data table (its first column did not wrap and pushed the others off the page), an underscore in the skeleton, the author line, and the float placement (figures now sit next to their text instead of after the references). The draft is 12 pages. Overleaf (pdfLaTeX + BibTeX) should give the same result.
