# Deployment Guide

This guide covers a simple MVP/demo deployment for the Heat Stress Risk Screening Dashboard.

## 1. Local Production-Like Run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Open the sidebar, enable **Show admin/demo tools**, then click **Load Client Demo Data** to populate the dashboard.

## 2. Required Files

Make sure these files are present in the deployment bundle:

```text
app.py
requirements.txt
.streamlit/config.toml
artifacts/models/heatstroke_model.joblib
demo_data/sample_assessments.csv
artifacts/data/synthetic_heatstroke_dataset.csv
core/
services/
storage/
views/
scripts/
```

## 3. Environment Variables

The app works without environment variables, but these are supported:

```bash
HEATSTROKE_DB_PATH=/persistent/path/heatstroke_records.db
APP_ENV=demo
ENABLE_DEMO_DATA=1
```

Use `HEATSTROKE_DB_PATH` when deploying to a platform with a mounted persistent volume. If omitted, SQLite writes to `./runtime/heatstroke_records.db`.

## 4. Streamlit Cloud Notes

For Streamlit Cloud:

1. Push the repository with `requirements.txt` and `.streamlit/config.toml`.
2. Set the app entrypoint to `app.py`.
3. Keep `artifacts/models/heatstroke_model.joblib` in the repository or regenerate it before deployment.
4. Load demo data from the sidebar after the app starts.

SQLite files may reset on some hosted platforms. For a durable deployment, point `HEATSTROKE_DB_PATH` at persistent storage or replace SQLite with a managed database.

## 5. Hugging Face Spaces Notes

For Hugging Face Spaces:

1. Create a Streamlit Space.
2. Upload the repository contents.
3. Ensure `requirements.txt` is present.
4. Use `app.py` as the Streamlit entrypoint.

Large NLP/model dependencies may increase cold-start time. The symptom parser has a keyword fallback if the transformer model is unavailable.

## 6. Demo Checklist

Before presenting:

- Run `python -m unittest discover -s tests`.
- Start `streamlit run app.py`.
- Load client demo data from the sidebar.
- Confirm the Monitoring Dashboard shows high-risk queue records.
- Run one Live Screening example with a high-risk case.
- Open Scenario Simulator and run a small custom cohort.

## 7. Safety Note

This is a decision-support demo, not a medical device or diagnosis system. High-risk outputs should trigger human review, cooling steps, and emergency response when red-flag symptoms are present.
