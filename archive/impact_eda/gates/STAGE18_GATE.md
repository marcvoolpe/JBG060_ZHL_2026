# Stage 18 gate — Session A figures and close-out

- Notebook: `session_a_figures.ipynb` → `figures/session_a/`
- Close-out: `SESSION_A_CLOSEOUT.md`

Execute notebook after stages 15–17:

```powershell
python -m eda.impact_session_a --through 18
jupyter nbconvert --execute eda/session_a_figures.ipynb
```