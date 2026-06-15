# Current Architecture — Clinical Heatstroke AI Predictor

This document outlines the current state and structure of the **Clinical Heatstroke AI Predictor** project.

## Directory Overview

The project repository contains the following files:

```
HHeatstroke project/
├── app.py                      # Streamlit frontend dashboard (3 tabs)
├── database.py                 # SQLite database integration for saving screening records
├── model.py                    # Inference API to load and query the Random Forest model
├── model_trainer.py            # Script for generating synthetic data and training the classifier
├── weather.py                  # API helper to fetch live weather data via wttr.in
├── ui_helpers.py               # Custom UI stylesheet injections, Browser Speech, recommendation logic
├── requirements.txt            # Project python dependencies
├── heatstroke_model.joblib     # Pre-trained Random Forest model state
├── heatstroke_records.db       # Local SQLite database containing patient records
└── synthetic_heatstroke_dataset.csv # The synthetic dataset used for model training
```

---

## Component Details

### 1. User Interface & Presentation Layer (`app.py` & `ui_helpers.py`)
- **Framework:** [Streamlit](https://streamlit.io/) is used to serve the web application.
- **Styling:** Injected premium custom CSS via [ui_helpers.py](file:///Users/mac/Downloads/HHeatstroke%20project/ui_helpers.py) using the Outfit font, glassmorphism card containers, custom buttons, alerts, and badges.
- **Voice Synthesis:** Uses the Web Speech API via `streamlit.components.v1` to read risk prediction alerts directly inside the browser using client-side JavaScript text-to-speech.
- **Interactions:**
  - **Tab 1: AI Diagnostic Screening:** Inputs environmental details (ambient temp, humidity, with city weather lookup fallback) and physiological metrics (age, height, weight for BMI, heart rate, body temp, water intake, active symptoms). Runs predictions, saves results, triggers voice response, and shows risk gauge.
  - **Tab 2: Data Science & ML Analytics:** Aggregates metrics from SQLite, visualizes distributions and trends using Plotly (Pie, Scatter, Line, Feature Importance bar charts), and provides log tabular views.
  - **Tab 3: Medical Safety Portal:** Explains Heat Exhaustion and Heat Stroke symptoms and first-aid measures.

### 2. Database Layer (`database.py` & `heatstroke_records.db`)
- **Database Engine:** SQLite (python's built-in `sqlite3`).
- **Tables:**
  - `heatstroke_records`: Schema details:
    - `id` (Primary Key Auto-Increment)
    - `timestamp` (DATETIME)
    - `patient_name` (TEXT)
    - `age`, `dizziness`, `headache` (INTEGER)
    - `body_temp`, `water_intake`, `outdoor_temp`, `humidity`, `heat_index`, `calculated_bmi`, `confidence` (REAL)
    - `predicted_risk` (TEXT: "LOW", "MEDIUM", "HIGH")
- **Functions:**
  - `init_db()`: Creates the table structure if missing.
  - `save_record(...)`: Appends a diagnostic assessment.
  - `get_all_records()`: Queries logs, sorting by time descending (returns list of row dicts).
  - `clear_database()`: Resets logs table.

### 3. Machine Learning Layer (`model.py`, `model_trainer.py`, `heatstroke_model.joblib`)
- **Algorithm:** Scikit-Learn `RandomForestClassifier` (100 estimators, max depth of 8).
- **Features:** 9 features: `Age`, `BodyTemp`, `WaterIntake`, `Dizziness`, `Headache`, `HeartRate`, `OutdoorTemp`, `Humidity`, `HeatIndex`.
- **Target Variable (`Risk`):** 
  - `0`: Low Risk
  - `1`: Medium Risk
  - `2`: High Risk
- **Data Generation:** Generates `1000` samples synthetically using medical logic based on risk scoring (body temperature, low hydration, active symptoms, heart rate, heat index, and age vulnerability).
- **Inference (`predict_risk_ml`):** Automatically computes environmental Heat Index using the Rothfusz regression model, runs RF classifier, returns probabilities, and maps output class to `"LOW"`, `"MEDIUM"`, or `"HIGH"`.

### 4. Integration Helpers (`weather.py`)
- **API Engine:** Free keyless API `https://wttr.in/{city}?format=j1`.
- **Parsing:** Obtains temperature (`temp_C`), relative humidity (`humidity`), and weather description.
- **Fail-safe:** Gracefully falls back to a default hot-weather simulation (35°C, 45% humidity) in case of offline states or HTTP timeouts.
