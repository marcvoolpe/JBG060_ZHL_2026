"""
Start a new area or country (REUSE.md): a clean copy of the pipeline, code only, none of our data.

    python cropland/make_new_area.py <folder>

makes <folder>/cropland/ with the steps 03-12, the shared modules, the labelling tool (no images,
no points), the guides and config/ (with TEMPLATE.toml). Our sample, labels, features, rules
and results stay here. Then: copy config/TEMPLATE.toml to config/<name>.toml, fill it in, and
follow REUSE.md from step 2.
"""

import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["03_agreement_and_sample.py", "04_image_strips.py", "05_features.py", "06_merge_labels.py",
         "07_fit_rules.py", "08_run_map.py", "09_score.py", "11_evaluate.py", "12_other_models.py"]
MODULES = ["common.py", "features.py", "rules.py", "estimators.py", "evaluation.py", "efficiency.py",
           "model_data.py", "label_server.py", "make_new_area.py"]
DOCS = ["REUSE.md", "METHODOLOGY.md", "LABELLING_GUIDE.md", "requirements-cropland.txt"]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    dst = Path(sys.argv[1]).resolve() / "cropland"
    if dst.exists():
        raise SystemExit(f"{dst} exists already")
    (dst / "label_tool").mkdir(parents=True)
    (dst / "labels").mkdir()
    for name in STEPS + MODULES + DOCS:
        shutil.copy2(HERE / name, dst / name)
    shutil.copytree(HERE / "config", dst / "config")
    shutil.copy2(HERE / "label_tool" / "index.html", dst / "label_tool" / "index.html")
    (dst / "label_tool" / "examples.js").write_text("window.EXAMPLES = [];\n", encoding="utf-8")
    print(f"clean pipeline in {dst}\nnext: copy config/TEMPLATE.toml to config/<name>.toml, fill it in, "
          f"set CROPLAND_CONFIG=<name>, and follow REUSE.md from step 2")


if __name__ == "__main__":
    main()
