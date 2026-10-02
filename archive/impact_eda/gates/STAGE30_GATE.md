# Stage 30 gate — Session D figures and close-out

- `session_d_figures.ipynb` → `figures/session_d/`
- `SESSION_D_CLOSEOUT.md` (includes ZOA/ZHL recommendation)

```powershell
python -m eda.impact_session_d --through 30
jupyter nbconvert --execute eda/session_d_figures.ipynb
```