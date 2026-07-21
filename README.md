# AUiX Network Map

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

The app reads `Streamlit.xlsx` from the same folder.

Expected columns:

- `name`
- `type`
- `engagement` or `engagament`
- `relationship`
- `Expertise`

## Interaction

- Click a category hub to show its organizations.
- Only one category is open at a time so labels remain readable.
- Click an organization to pin its details in the right-hand panel.
- Click that organization again to close its details.
- Click AUiX to collapse the map.
