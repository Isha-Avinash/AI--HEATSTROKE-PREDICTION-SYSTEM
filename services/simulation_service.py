import numpy as np
import pandas as pd
import uuid

from storage.database import log_audit_event, save_record
from core.risk_rules import RULE_ENGINE_VERSION, apply_safety_overrides
from services.model_service import get_model_metadata, predict_risk_ml
from services.training_service import calculate_heat_index

SCENARIO_PROFILES = {
    "Heatwave Delhi": {
        "outdoor_temp": (41.0, 48.0),
        "humidity": (12.0, 35.0),
        "water_intake": (0.5, 1.8),
        "body_temp": (37.2, 41.5),
        "heart_rate": (80, 145),
        "symptoms": {
            "dizziness": 0.40,
            "headache": 0.45,
            "muscle_cramps": 0.45,
            "nausea": 0.35,
            "confusion": 0.20
        }
    },
    "Monsoon Mumbai": {
        "outdoor_temp": (31.0, 36.0),
        "humidity": (75.0, 95.0),
        "water_intake": (1.0, 2.5),
        "body_temp": (36.8, 38.8),
        "heart_rate": (75, 120),
        "symptoms": {
            "dizziness": 0.20,
            "headache": 0.25,
            "muscle_cramps": 0.25,
            "nausea": 0.18,
            "confusion": 0.04
        }
    },
    "Normal Bangalore": {
        "outdoor_temp": (23.0, 29.0),
        "humidity": (40.0, 65.0),
        "water_intake": (2.0, 4.0),
        "body_temp": (36.3, 37.2),
        "heart_rate": (60, 90),
        "symptoms": {
            "dizziness": 0.05,
            "headache": 0.05,
            "muscle_cramps": 0.03,
            "nausea": 0.02,
            "confusion": 0.01
        }
    }
}

def get_scenario_profile(scenario):
    """Returns a copy of a predefined scenario profile."""
    profile = SCENARIO_PROFILES.get(scenario, SCENARIO_PROFILES["Normal Bangalore"])
    return {
        "outdoor_temp": tuple(profile["outdoor_temp"]),
        "humidity": tuple(profile["humidity"]),
        "water_intake": tuple(profile["water_intake"]),
        "body_temp": tuple(profile["body_temp"]),
        "heart_rate": tuple(profile["heart_rate"]),
        "symptoms": dict(profile["symptoms"])
    }

def run_cohort_simulation(n_patients, scenario, profile=None, random_seed=None):
    """
    Simulates a cohort of patients under specific climate scenarios.
    Runs predictions on each patient, logs records to SQLite, and returns a summary.
    """
    active_profile = profile or get_scenario_profile(scenario)
    batch_id = f"sim_{scenario.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}"
    
    rng = np.random.default_rng(random_seed)
    model_metadata = get_model_metadata()
    metrics = model_metadata.get("metrics", {})

    temp_min, temp_max = active_profile["outdoor_temp"]
    hum_min, hum_max = active_profile["humidity"]
    water_min, water_max = active_profile["water_intake"]
    body_temp_min, body_temp_max = active_profile["body_temp"]
    hr_min, hr_max = active_profile["heart_rate"]
    symptom_probs = active_profile["symptoms"]

    records = []
    
    for idx in range(n_patients):
        patient_name = f"Sim_{scenario.replace(' ', '')}_{idx+1}"
        age = int(rng.integers(8, 80))
        weight = float(np.round(rng.uniform(45.0, 105.0), 1))
        height = float(np.round(rng.uniform(1.45, 1.95), 2))
        bmi = round(weight / (height ** 2), 2)
        
        outdoor_temp = float(np.round(rng.uniform(temp_min, temp_max), 1))
        humidity = float(np.round(rng.uniform(hum_min, hum_max), 1))
        water_intake = float(np.round(rng.uniform(water_min, water_max), 1))
        body_temp = float(np.round(rng.uniform(body_temp_min, body_temp_max), 1))
        heart_rate = int(rng.integers(hr_min, hr_max))
        
        dizziness = int(rng.choice([0, 1], p=[1 - symptom_probs["dizziness"], symptom_probs["dizziness"]]))
        headache = int(rng.choice([0, 1], p=[1 - symptom_probs["headache"], symptom_probs["headache"]]))
        muscle_cramps = int(rng.choice([0, 1], p=[1 - symptom_probs["muscle_cramps"], symptom_probs["muscle_cramps"]]))
        nausea = int(rng.choice([0, 1], p=[1 - symptom_probs["nausea"], symptom_probs["nausea"]]))
        confusion = int(rng.choice([0, 1], p=[1 - symptom_probs["confusion"], symptom_probs["confusion"]]))
        
        heat_index = calculate_heat_index(outdoor_temp, humidity)
        
        # Predict using local ML model
        pred_res = predict_risk_ml(
            age=age,
            body_temp=body_temp,
            water_intake=water_intake,
            dizziness=dizziness,
            headache=headache,
            heart_rate=heart_rate,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            muscle_cramps=muscle_cramps,
            nausea=nausea,
            confusion=confusion
        )
        
        ml_risk = pred_res["predicted_risk"]
        confidence = pred_res["confidence"]
        safety_result = apply_safety_overrides(
            ml_risk=ml_risk,
            confidence=confidence,
            body_temp=body_temp,
            heat_index=heat_index,
            water_intake=water_intake,
            heart_rate=heart_rate,
            dizziness=dizziness,
            headache=headache,
            muscle_cramps=muscle_cramps,
            nausea=nausea,
            confusion=confusion,
        )
        final_risk = safety_result["final_risk"]
        
        # Save results to database
        save_record(
            patient_name=patient_name,
            age=age,
            body_temp=body_temp,
            water_intake=water_intake,
            dizziness=dizziness,
            headache=headache,
            heart_rate=heart_rate,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            heat_index=heat_index,
            calculated_bmi=bmi,
            predicted_risk=final_risk,
            confidence=confidence,
            height_m=height,
            weight_kg=weight,
            muscle_cramps=muscle_cramps,
            nausea=nausea,
            confusion=confusion,
            simulation_batch_id=batch_id,
            ml_risk=ml_risk,
            final_risk=final_risk,
            safety_override_applied=safety_result["override_applied"],
            safety_override_reasons=safety_result["override_reasons"],
            model_type=model_metadata.get("model_type", "N/A"),
            model_training_date=model_metadata.get("training_date", "N/A"),
            model_accuracy=metrics.get("accuracy"),
            rule_engine_version=safety_result["rule_engine_version"]
        )
        
        records.append({
            "patient_name": patient_name,
            "age": age,
            "outdoor_temp": outdoor_temp,
            "humidity": humidity,
            "body_temp": body_temp,
            "water_intake": water_intake,
            "heart_rate": heart_rate,
            "heat_index": heat_index,
            "dizziness": dizziness,
            "headache": headache,
            "muscle_cramps": muscle_cramps,
            "nausea": nausea,
            "confusion": confusion,
            "ml_risk": ml_risk,
            "predicted_risk": final_risk,
            "final_risk": final_risk,
            "confidence": confidence,
            "safety_override_applied": safety_result["override_applied"],
            "safety_override_reasons": safety_result["override_reasons"],
            "rule_engine_version": safety_result["rule_engine_version"]
        })
        
    df_results = pd.DataFrame(records)
    
    risk_counts = df_results["predicted_risk"].value_counts().to_dict()
    for r in ["LOW", "MEDIUM", "HIGH"]:
        if r not in risk_counts:
            risk_counts[r] = 0
            
    summary = {
        "batch_id": batch_id,
        "total_simulated": n_patients,
        "risk_counts": risk_counts,
        "avg_body_temp": round(float(df_results["body_temp"].mean()), 2),
        "avg_water_intake": round(float(df_results["water_intake"].mean()), 2),
        "avg_heat_index": round(float(df_results["heat_index"].mean()), 2),
        "avg_heart_rate": round(float(df_results["heart_rate"].mean()), 2),
        "avg_confidence": round(float(df_results["confidence"].mean()), 2),
        "random_seed": random_seed,
        "scenario_profile": active_profile,
        "records": records
    }

    log_audit_event(
        "simulation_batch_completed",
        entity_type="batch",
        entity_id=batch_id,
        details={
            "scenario": scenario,
            "total_simulated": n_patients,
            "risk_counts": risk_counts,
            "random_seed": random_seed,
            "model_type": model_metadata.get("model_type", "N/A"),
            "model_training_date": model_metadata.get("training_date", "N/A"),
            "rule_engine_version": RULE_ENGINE_VERSION,
        },
    )
    
    return summary
