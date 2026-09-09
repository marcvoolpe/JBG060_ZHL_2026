# Data families and AA role

From Data_overview.xlsx. Wei already covers flood mask structure in detail.

| Family | AA role | What it is | Limit |
|--------|---------|------------|-------|
| flood_masks | hazard | daily flooded pixels, recurring vs unusual | unusual != severity or damage |
| worldpop | exposure: inhabitants | people per ~100m cell, yearly | model estimate, not census |
| asap crop | exposure: farmers (cropland) | static 0-100% crop cover ~500m | one map, not yearly |
| asap rangeland | exposure: grazing land | static 0-100% rangeland | same |
| cattle | exposure: livestock | GHA cattle raster ~2010 | old |
| IPC | impact proxy | food insecurity phase counts | few dates per year |
| ERA5 rain/runoff | driver / lead time | hourly tp, ro | reanalysis, not gauges |
| lake levels | driver upstream | Victoria, Kyoga, Albert | Hydroweb parsing can spike |
| discharge | driver | Dartmouth stations | few points |
| health facilities | impact access | facility points | completeness unknown |
| admin0-3 | local units | country / state / county / payam | needed to talk "local" |
| GDP | weak context | national only | not local AA |

Admin levels (COD-AB South Sudan):
- **admin0** = country outline
- **admin1** = states (e.g. Jonglei, Upper Nile)
- **admin2** = counties (e.g. Fangak, Twic East). These are the "admin counties" in the notebook
- **admin3** = payams (`admin3_payams.ipynb`; no IPC at this level)

We aggregate floods to counties because ZOA/ZHL care about local farmers and inhabitants, not only a national pixel total.
