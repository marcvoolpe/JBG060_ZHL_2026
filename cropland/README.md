# cropland/

Cropland-accuracy work (Sprint 3-4). Full plan: `deliverables/CROPLAND_PLAN.html`.

## Now: the pilot (does labelling by eye work here?)

| step | script / file | what it does |
|---|---|---|
| 0 | `00_pilot_points.py` | 30 random points in Twic county (outside the study areas), fixed seed → `pilot_points.csv`, `pilot_points.kml`, `pilot_labels_TEMPLATE.csv` |
| – | `LABELLING_GUIDE.md` | how to label a point, what counts as crop, the traps |
| 1 | `01_compare_pilot.py` | agreement and Cohen's kappa between labellers, share of confident labels |
| 2 | `02_strata_from_asap.py` | first look at crop share per county from the ASAP mask on disk → `asap_crop_share_by_county.csv` |

Run from `group_repo` with the project environment (`pip install -r requirements.txt`), e.g. `python cropland/01_compare_pilot.py`.

Go / no-go: if fewer than ~70% of pilot points get a confident crop / not-crop label, switch to "share of crop per 100 m cell" instead of point labels.

Earth Engine steps (agreement map, real sample, features, rules, map) come next and need a Google account registered for non-commercial Earth Engine use.
