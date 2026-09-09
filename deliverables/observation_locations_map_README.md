# Observation Locations Map

This map is a spatial sanity check for the hydrological and climate data used in the EDA.

- Dartmouth discharge data contain 12 station points. Only station 100205 is inside/near South Sudan; most others are downstream in Sudan or upstream in Ethiopia.
- Lake water-level data contain three representative lake points: Albert, Kyoga, and Victoria. All are outside South Sudan, so they should be treated as upstream/regional context rather than local South Sudan lake gauges.
- ERA5 rainfall/runoff raw data are gridded over a broad domain, but the processed file currently stores one daily spatial mean.
- ET raw data are also gridded. The previous single-cell ET marker is intentionally not shown because it is not a meaningful observation location for the main analysis.
- The local flood mask data cover h20v08 and h21v08, approximately lon 20E-40E and lat 0N-10N; this misses northern South Sudan above 10N.
- Major river, lake, and surrounding-country layers come from Natural Earth 1:10m data downloaded into raw_data/external_geography/natural_earth.
- climate_grid_points_context_map.png shows all ERA5 grid nodes and all ET grid nodes to make the difference in spatial resolution visible.
