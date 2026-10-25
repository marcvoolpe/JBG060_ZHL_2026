"""
The code submission as one zip: README.md at the top, then the files the notebook needs and writes.

Takes only files git tracks, so no labelling images, no course data and no eda/national.npz (README,
section 4.3): all of cropland/ and raw_data/cropland/, and the outputs in deliverables/cropland_report/
(figures, tables, maps, dashboard). Left out: the LaTeX report and its scripts (report/) and the team's
working guide (cropland/README.md); this folder's README.md becomes the zip's README.md.
METHODOLOGY.md goes in as the method fixed before labelling (sections 1-9), without the team's
deadlines and its change log, which stay in the repository.

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
LEAVE_OUT = {"cropland/README.md"}                        # the team's working guide; the zip's README replaces it
METHOD, METHOD_END = "cropland/METHODOLOGY.md", "## 10. Deadlines"
OUT = HERE / "group1_cropland_code.zip"


def main() -> None:
    listed = subprocess.run(["git", "ls-files", "--", *KEEP], cwd=REPO, capture_output=True, text=True, check=True).stdout
    files = [f for f in listed.splitlines() if (REPO / f).is_file() and f not in LEAVE_OUT]   # deleted but not committed: skipped
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "README.md", "README.md")
        for f in files:
            if f == METHOD:                                # sections 1-9 only
                text = (REPO / f).read_bytes().decode("utf-8")
                z.writestr(f, text[:text.index(METHOD_END)].rstrip() + "\n")
            else:
                z.write(REPO / f, f)
    print(f"{OUT.name}: README.md and {len(files)} files, {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
