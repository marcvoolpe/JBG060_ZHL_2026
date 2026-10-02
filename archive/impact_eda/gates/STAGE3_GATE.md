# Stage 3 gate — spatial-temporal crosswalks

## Artefacts

| Output | Path |
|--------|------|
| Admin2 name/P-code crosswalk | `outputs/impact_eda/crosswalks/admin2_names.csv` |
| FEWS fnid → county | `outputs/impact_eda/crosswalks/fews_fnid_to_admin2.csv` |
| Admin1 (ACLED) | `outputs/impact_eda/crosswalks/admin1_names.csv` |
| Match rates | `outputs/impact_eda/crosswalks/crosswalk_match_rates.csv` |
| Unmatched admin2 names | `outputs/impact_eda/crosswalks/admin2_unmatched.csv` |
| Time units | `outputs/impact_eda/temporal_alignment.md` |

## Regenerate

```powershell
python -m eda.impact_stages --through 3
```

## Gate checklist

- [x] COD `adm2_pcode` used as canonical county key.
- [x] DTM R16 matched by P-code where names differ.
- [x] OCHA 20251130 counties included with P-codes.
- [x] FEWS `fnid` linked via county name crosswalk.
- [x] ACLED admin1 ↔ COD admin1 table (county flood must aggregate **up** to state).
- [ ] **Team review:** inspect `admin2_unmatched.csv` before county-level joins in Stage 6–7.

## Typical unmatched (expect these)

- IPC: `Returnees`, `Akoka` (if not in COD-AB list), `Abyei region` edge cases
- FEWS: `Abyei`, `Akoka` (extra FEWS units vs 79 COD counties)
- UCDP: counties in UCDP spelling not in COD (e.g. `Bor North county` if absent from COD)

## Next step

Stage 4 — redundancy matrix: `python -m eda.impact_stages --through 4`
