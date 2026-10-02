"""Record the JRC ASAP crop and rangeland masks (already in the course pack) in the manifest.

Nothing is downloaded or copied: the files stay in the course pack under
farmland/. This script only logs provenance, checksums and grid facts.

Usage (repo root, global Python 3.13):
    python -m processing_data.cropland.document_asap
"""

from __future__ import annotations

from processing_data.cropland.common import file_fields, today, upsert_manifest
from processing_data.paths import COURSE_RAW

SOURCE = ("JRC ASAP download page https://agricultural-production-hotspots.ec.europa.eu/download.php "
          "(course pack copy: farmland/)")
CITATION = ("Fritz, S., Lesiv, M., Perez Guzman, K., See, L., Meroni, M., Collivignarelli, F. and Rembold, F. (2024). "
            "Development of a new cropland and rangeland Area Fraction Image at 500 m for the ASAP system. "
            "Publications Office of the European Union, Luxembourg. doi:10.2760/32935")


def main() -> None:
    for cover in ("crop", "rangeland"):
        path = COURSE_RAW / "farmland" / f"asap_mask_{cover}_v04.tif"
        row = dict(product=f"JRC ASAP {cover} mask", version="v04 (last updated 01-12-2023)", year="static",
                   aoi="global (course pack file)", source=SOURCE, access_date=today(), band="band 1",
                   class_codes=f"% of the pixel covered by {'temporary crops' if cover == 'crop' else 'rangeland'} "
                               "(0-100); no no-data tag in the file",
                   ee_task_id="n/a", export_params={"note": "not downloaded: course-pack file documented in place"},
                   status="obtained (course pack)",
                   notes=f"~500 m (1/224 deg) area-fraction image combining existing maps. {CITATION}")
        row.update(file_fields(path))
        upsert_manifest(row)
        print(f"logged {path.name}: {row['file_size_bytes'] / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
