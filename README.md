# Heat Stress Risk Screening Dashboard

An interactive Streamlit MVP for heat-illness risk screening, monitoring, scenario simulation, and safety response. The system combines a local ML model, conservative safety rules, patient memory, follow-up workflows, audit logging, and cohort-level analytics.

> This project is an educational decision-support demo. It is not a medical device, diagnosis system, or replacement for trained responders. If someone has confusion, collapse, loss of consciousness, or very high body temperature, start cooling and seek emergency medical care immediately.

## What The App Does

- Screens heat-stress risk from environment, vitals, hydration, and symptoms
- Parses natural-language symptom descriptions and lets the user confirm detections
- Calculates apparent temperature / heat index
- Uses a hybrid risk engine: ML prediction plus safety-rule overrides
- Shows key factors behind each result
- Saves assessments to a local SQLite database
- Remembers patient history using Patient Name / ID + Age + Height
- Adds response/follow-up action checklists and reassessment timing
- Tracks high-priority cases in a monitoring dashboard
- Shows patient timelines, follow-up status, analytics, and audit events
- Runs reproducible scenario simulations for client demos
- Includes safety protocol guidance for heat illness response

## Project Structure

```text
app.py                         Main Streamlit app and page workflow
core/                          Risk rules, risk drivers, and explainability helpers
services/                      Prediction, simulation, NLP, weather, workflow, and training services
storage/database.py            SQLite schema, migrations, assessment storage, audit logs, follow-ups
views/                         Header, sidebar, safety protocols, and reusable UI helpers
scripts/train_model.py         Model training command
artifacts/models/              Trained model artifact
artifacts/data/                Generated synthetic training dataset
data/clinical/                 Reference/demo clinical-style datasets
demo_data/                     Client demo seed records
docs/                          Deployment, demo flow, and architecture notes
runtime/                       Local SQLite runtime database
tests/test_core.py             Core smoke/regression tests
.streamlit/config.toml         Streamlit runtime configuration
.env.example                   Example environment variables
requirements.txt               Python dependencies
```

## First-Time Setup

Run these commands from the project folder.

```bash
cd "/Users/mac/Downloads/HHeatstroke project"
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional: create a local environment file from the example:

```bash
cp .env.example .env
```

The app can run without editing `.env`. By default, records are stored here:

```text
runtime/heatstroke_records.db
```

## Run The App

Start Streamlit:

```bash
streamlit run app.py
```

If `streamlit` is not found, run it through Python:

```bash
python -m streamlit run app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Demo Flow

1. Open **Live Screening**.
2. Enter a patient/person ID, age, height, weight, vitals, hydration, and symptoms.
3. Optionally describe symptoms in natural language and click **Check symptoms**.
4. Review and apply detected symptoms.
5. Click **Run Heat Stress Screening**.
6. Review the risk result, confidence, key factors, and suggested next actions.
7. Save response/follow-up actions and reassessment timing.
8. Open **Monitoring Dashboard**.
9. Review priority cases, reassessment alerts, patient timeline, follow-up status, analytics, and audit log.
10. Open **Scenario Simulator**.
11. Run a preset or custom cohort scenario and download the scenario report.
12. Open **Safety Protocols** for heat illness response guidance.

For a fuller walkthrough, see:

```text
docs/demo_flow.md
```

## Load Demo Data

Open the sidebar in the app, enable:

```text
Show admin/demo tools
```

Then click:

```text
Load Client Demo Data
```

This seeds sample records from:

```text
demo_data/sample_assessments.csv
```

Use this when you want the Monitoring Dashboard to show useful records immediately.

## Train Or Rebuild The Model

The app already includes a trained model:

```text
artifacts/models/heatstroke_model.joblib
```

If the model file is missing or you want to regenerate it:

```bash
python scripts/train_model.py
```

Training regenerates:

```text
artifacts/models/heatstroke_model.joblib
artifacts/data/synthetic_heatstroke_dataset.csv
```

## Run Tests

Run the regression tests:

```bash
python -m unittest discover -s tests
```

Expected result:

```text
Ran 14 tests
OK
```

Some macOS or sandboxed environments may print PyArrow CPU-info warnings. They are harmless if the tests still end with `OK`.

## Environment Configuration

By default, the app writes the local SQLite database to:

```text
runtime/heatstroke_records.db
```

To use a custom database path:

```bash
export HEATSTROKE_DB_PATH="/absolute/path/to/heatstroke_records.db"
streamlit run app.py
```

The database initializes and migrates automatically when the app starts.

## Current Intelligence Layer

The system is more than a single prediction screen. It now includes:

- Patient profile memory using name, age, and height
- Triage priority scoring for urgent monitoring
- Reassessment alerts based on risk and follow-up timing
- Response action checklist for low, medium, and high risk
- Follow-up action storage
- Follow-up status badges in patient timeline
- Audit events for recorded assessments, simulations, and follow-ups
- Reproducible scenario simulation with random seed support

## Model And Safety Notes

The current ML model is trained on synthetic clinical-style data generated by:

```text
services/training_service.py
```

The final displayed risk is produced by:

```text
Final Risk = ML estimate + conservative safety-rule overrides
```

Safety rules can raise risk when red flags are present, including:

- Confusion / delirium
- Very high internal body temperature
- Extreme heat index with active symptoms
- High body temperature plus high heart rate and low hydration

This is intentional: in a safety workflow, red flags should not be hidden behind a lower model probability.

## Troubleshooting

If Streamlit shows an old import error after code changes, stop the server with `Ctrl+C` and restart:

```bash
streamlit run app.py
```

If a NumPy/joblib model loading error appears, rebuild the model:

```bash
python scripts/train_model.py
streamlit run app.py
```

If patient memory does not update immediately after typing a name, press Enter or click outside the input so Streamlit reruns the page.

## Deployment

Deployment notes are available here:

```text
docs/deployment.md
```

Deployment-ready files include:

- `.streamlit/config.toml`
- `.env.example`
- `requirements.txt`
- `demo_data/sample_assessments.csv`
- `docs/deployment.md`

## Limitations

- The model is not clinically validated.
- The dataset is synthetic/demo-oriented.
- The NLP parser uses transformer matching when available and falls back to keywords.
- The app is suitable for academic, prototype, and client-demo use, not autonomous medical triage.
