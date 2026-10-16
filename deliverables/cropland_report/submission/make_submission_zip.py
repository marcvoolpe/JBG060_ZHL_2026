"""
The code submission as one zip: README.md at the top, then the files the notebook needs and writes.

Takes only files git tracks, so no labelling images, no course data and no eda/national.npz (README,
section 3): all of cropland/ and raw_data/cropland/, and the outputs in deliverables/cropland_report/
(figures, tables, maps, dashboard). The LaTeX report and its scripts (report/) are not part of it.
This folder's README.md becomes the zip's README.md.

Run from the repository root: python deliverables/cropland_report/submission/make_submission_zip.py
Writes deliverables/cropland_report/submission/group1_cropland_code.zip (not in git: *.zip is ignored).
"""

import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KEEP = ["cropland", "raw_data/cropland", "deliverables/cropland_report/dashboard.html"] + [
    f"deliverables/cropland_report/{d}" for d in ("figures", "tables", "maps")]
OUT = HERE / "group1_cropland_code.zip"


def main() -> None:
    listed = subprocess.run(["git", "ls-files", "--", *KEEP], cwd=REPO, capture_output=True, text=True, check=True).stdout
    files = [f for f in listed.splitlines() if (REPO / f).is_file()]      # a file deleted but not yet committed is skipped
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "README.md", "README.md")
        for f in files:
            z.write(REPO / f, f)
    print(f"{OUT.name}: README.md and {len(files)} files, {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
