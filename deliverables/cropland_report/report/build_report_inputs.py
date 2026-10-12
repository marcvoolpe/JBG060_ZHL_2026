"""
Prepare the LaTeX report for Overleaf:
  1. numbers.tex: one macro per number the report quotes, read from the notebook's
     key_numbers.csv, so no number in the text is typed by hand (rerun after the
     notebook, and the report follows);
  2. figures/: copies of the notebook's figures;
  3. overleaf_upload.zip: report.tex, references.bib, numbers.tex and figures/,
     ready for Overleaf (New project > Upload project).

Run from the repo root: python deliverables/cropland_report/report/build_report_inputs.py
"""

import shutil
import zipfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
TABLES = HERE.parent / "tables"
FIGURES = HERE.parent / "figures"

pct2, pct1, pct0 = "{:.2f}\\%", "{:.1f}\\%", "{:.0f}\\%"
ha, two, sign, one = "{:,.0f}", "{:.2f}", "{:+.2f}", "{:.1f}"
NUMBERS = {   # key in key_numbers.csv -> (macro name, format)
    "Aweil crop share, lowest map (%)": ("AwCropMin", pct2),
    "Aweil crop share, highest map (%)": ("AwCropMax", pct2),
    "Aweil CFSAM 2025 cereal area (% of land)": ("AwCfsamTwentyFive", pct1),
    "Aweil CFSAM 2022 cereal area (% of land)": ("AwCfsamTwentyTwo", pct1),
    "Bor South crop share, Dynamic World 2025 (%)": ("BsDwShare", pct1),
    "Bor South crop share, highest other map (%)": ("BsOtherMax", pct2),
    "Aweil land no map calls crop (%)": ("AwNoMap", pct1),
    "Aweil land all 7 maps call crop (ha)": ("AwAllSevenHa", one),
    "Aweil land >= 4 maps call crop (%)": ("AwMajority", pct2),
    "Aweil pairwise IoU, best pair": ("AwIoUMax", two),
    "Aweil pairwise IoU, median pair": ("AwIoUMedian", two),
    "National crop, lowest map (Mha)": ("NatCropMin", two),
    "National crop, highest map (Mha)": ("NatCropMax", two),
    "National CFSAM 2025 cereal area (Mha)": ("NatCfsam", two),
    "National FAOSTAT arable land (Mha)": ("NatFaostat", two),
    "Aweil 2022 flooded cropland, lowest map (ha)": ("AwFloodMin", ha),
    "Aweil 2022 flooded cropland, highest map (ha)": ("AwFloodMax", ha),
    "National 2022 flooded cropland, lowest map (ha)": ("NatFloodMin", ha),
    "National 2022 flooded cropland, highest map (ha)": ("NatFloodMax", ha),
    "National 2022 flooded cropland, ASAP (ha)": ("NatFloodAsap", ha),
    "CFSAM 2022 cultivated land damaged by floods (ha)": ("CfsamDamaged", ha),
    "Bor South 2025 flooded cropland, Dynamic World (ha)": ("BsFloodDw", ha),
    "Bor South 2025 flooded cropland, all other maps (ha, max)": ("BsFloodOther", ha),
    "Labelled twice so far (points)": ("LabTwice", ha),
    "Labellers agree cropland vs not (%)": ("LabAgree", pct1),
    "Cohen's kappa cropland vs not": ("LabKappa", two),
    "Labellers agree cropland vs not, Aweil (%)": ("LabAgreeAw", pct1),
    "Cohen's kappa cropland vs not, Aweil": ("LabKappaAw", two),
    "Cohen's kappa cropland vs not, Bor South": ("LabKappaBs", two),
    "Labeller splits on cropland (points)": ("LabSplits", ha),
    "Splits where field shape answers differ (points)": ("LabShapeSplits", ha),
    "Esri F1 in Mali, Kerner et al. 2024": ("EsriMaliFone", two),
    "Esri accuracy in Mali, Kerner et al. 2024": ("EsriMaliAcc", two),
    "Rank corr. published recall (Kerner) vs Aweil crop share": ("RecallRhoAw", sign),
    "Rank corr. published recall (Kerner) vs Bor South crop share": ("RecallRhoBs", sign),
    "Aweil land (ha)": ("AwLandHa", ha),
    "Bor South land (ha)": ("BsLandHa", ha),
    "Usual interval coverage, lowest (%)": ("CovUsualMin", pct0),
    "Usual interval coverage, highest (%)": ("CovUsualMax", pct0),
    "Adjusted interval coverage, lowest (%)": ("CovAdjMin", pct0),
    "Adjusted interval coverage, lowest in Aweil (%)": ("CovAdjMinAw", pct0),
}


def write_numbers():
    key = pd.read_csv(TABLES / "key_numbers.csv", index_col=0).value
    lines = ["% Written by build_report_inputs.py from key_numbers.csv. Do not edit by hand.",
             "\\providecommand{\\ph}[1]{[#1]}"]
    for k, (name, fmt) in NUMBERS.items():
        text = fmt.format(float(key[k])) if k in key else f"\\ph{{missing: {k}}}"
        lines.append(f"\\newcommand{{\\{name}}}{{{text}}}")
    (HERE / "numbers.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = [k for k in NUMBERS if k not in key]
    print(f"numbers.tex: {len(NUMBERS) - len(missing)} numbers" + (f", missing: {missing}" if missing else ""))


def copy_figures():
    out = HERE / "figures"
    out.mkdir(exist_ok=True)
    for f in sorted(FIGURES.glob("*.png")):
        shutil.copy2(f, out / f.name)
    print(f"figures/: {len(list(out.glob('*.png')))} files")


def make_zip():
    z = HERE / "overleaf_upload.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ("report.tex", "references.bib", "numbers.tex"):
            zf.write(HERE / name, name)
        for f in sorted((HERE / "figures").glob("*.png")):
            zf.write(f, f"figures/{f.name}")
    print(f"{z.name}: ready for Overleaf (New project > Upload project)")


if __name__ == "__main__":
    write_numbers()
    copy_figures()
    make_zip()
