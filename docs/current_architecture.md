# Current Architecture

This project is now organized as a Streamlit MVP/client demo for heat-stress risk screening.

## Directory Overview

```text
app.py                         Streamlit entrypoint and tab composition
core/                          Domain logic
  risk_rules.py                Hybrid safety override rules
  risk_drivers.py              Human-readable risk driver logic
  explainability.py            Model-weighted explanation scoring
services/                      Application services
  model_service.py             Model loading, prediction, metadata, explanation wrapper
  prediction_service.py        Coordinates ML prediction + safety overrides + explanations
  weather_service.py           Live weather lookup
  symptom_service.py           NLP/keyword symptom parsing
  simulation_service.py        Cohort simulation
  risk_tracker_service.py      Patient timeline trend detection
  training_service.py          Synthetic data generation and model retraining
storage/
  database.py                  SQLite persistence, demo loading, audit log
views/
  header.py                    App heading and safety disclaimer
  sidebar.py                   Demo/admin/sidebar controls
  safety_protocols.py          Safety guidance tab
  ui_helpers.py                Shared Streamlit UI helpers and cards
artifacts/
  models/heatstroke_model.joblib
  data/synthetic_heatstroke_dataset.csv
data/clinical/                 Reference datasets, not active runtime inputs
demo_data/                     Client demo seed cohort
docs/                          Deployment and demo flow docs
runtime/                       Local SQLite runtime state
tests/                         Unit/smoke tests
```

`app.py` is the only root-level Python entrypoint. Implementation modules live under `core/`, `services/`, `storage/`, and `views/`.

## Runtime Flow

1. `app.py` initializes Streamlit and the SQLite database.
2. The sidebar can load curated demo data and expose admin tools.
3. Live Screening collects environment, vitals, hydration, and symptoms.
4. `services.prediction_service.run_screening()` coordinates:
   - ML prediction from `services.model_service`
   - safety overrides from `core.risk_rules`
   - risk drivers from `core.risk_drivers`
   - model explainability from `core.explainability`
5. `storage.database.save_record()` persists assessment metadata, final risk, ML risk, model version, safety-rule metadata, and audit events.
6. Monitoring Dashboard reads records and audit logs from SQLite.

## Data & Artifacts

- `artifacts/models/heatstroke_model.joblib` is required for runtime prediction.
- `artifacts/data/synthetic_heatstroke_dataset.csv` is a training artifact, not required at runtime if the model artifact exists.
- `demo_data/sample_assessments.csv` is used by the sidebar demo-data loader.
- `data/clinical/` contains reference datasets for future model improvement; they are not currently used by the live app.
- `runtime/heatstroke_records.db` is local runtime state and should not be treated as source code.
