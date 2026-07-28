# AUiX Network Map

Run locally:

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Updating the data

The app reads `Streamlit.xlsx` from the same folder as `app.py`. Changes made to another copy of the spreadsheet do not sync automatically. Replace this file locally, or upload and commit the revised file in GitHub for a deployed app.

A live Google Sheet connection can be added later if automatic updates are preferred.
