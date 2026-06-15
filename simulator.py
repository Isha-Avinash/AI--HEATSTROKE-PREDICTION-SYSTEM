import numpy as np
import pandas as pd
import uuid

from database import save_record
from model import predict_risk_ml
from model_trainer import calculate_heat_index

def run_cohort_simulation(n_patients, scenario):
    """
    Simulates a cohort of patients under specific climate scenarios.
    Runs predictions on each patient, logs records to SQLite, and returns a summary.
    """
    batch_id = f"sim_{scenario.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}"
    
    np.random.seed(None)  # Use random state dynamically
    
    # Define profiles: temp, humidity, water intake, body temp, symptoms
    if scenario == "Heatwave Delhi":
        temp_min, temp_max = 41.0, 48.0
        hum_min, hum_max = 12.0, 35.0
        water_min, water_max = 0.5, 1.8
        body_temp_min, body_temp_max = 37.2, 41.5
        hr_min, hr_max = 80, 145
        diz_p, head_p, cramp_p, nausea_p, conf_p = 0.40, 0.45, 0.45, 0.35, 0.20
    elif scenario == "Monsoon Mumbai":
        temp_min, temp_max = 31.0, 36.0
        hum_min, hum_max = 75.0, 95.0
        water_min, water_max = 1.0, 2.5
        body_temp_min, body_temp_max = 36.8, 38.8
        hr_min, hr_max = 75, 120
        diz_p, head_p, cramp_p, nausea_p, conf_p = 0.20, 0.25, 0.25, 0.18, 0.04
    else:  # "Normal Bangalore"
        temp_min, temp_max = 23.0, 29.0
        hum_min, hum_max = 40.0, 65.0
        water_min, water_max = 2.0, 4.0
        body_temp_min, body_temp_max = 36.3, 37.2
        hr_min, hr_max = 60, 90
        diz_p, head_p, cramp_p, nausea_p, conf_p = 0.05, 0.05, 0.03, 0.02, 0.01

    records = []
    
    for idx in range(n_patients):
        patient_name = f"Sim_{scenario.replace(' ', '')}_{idx+1}"
        age = int(np.random.randint(8, 80))
        weight = float(np.round(np.random.uniform(45.0, 105.0), 1))
        height = float(np.round(np.random.uniform(1.45, 1.95), 2))
        bmi = round(weight / (height ** 2), 2)
        
        outdoor_temp = float(np.round(np.random.uniform(temp_min, temp_max), 1))
        humidity = float(np.round(np.random.uniform(hum_min, hum_max), 1))
        water_intake = float(np.round(np.random.uniform(water_min, water_max), 1))
        body_temp = float(np.round(np.random.uniform(body_temp_min, body_temp_max), 1))
        heart_rate = int(np.random.randint(hr_min, hr_max))
        
        dizziness = int(np.random.choice([0, 1], p=[1 - diz_p, diz_p]))
        headache = int(np.random.choice([0, 1], p=[1 - head_p, head_p]))
        muscle_cramps = int(np.random.choice([0, 1], p=[1 - cramp_p, cramp_p]))
        nausea = int(np.random.choice([0, 1], p=[1 - nausea_p, nausea_p]))
        confusion = int(np.random.choice([0, 1], p=[1 - conf_p, conf_p]))
        
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
        
        risk = pred_res["predicted_risk"]
        confidence = pred_res["confidence"]
        
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
            predicted_risk=risk,
            confidence=confidence,
            muscle_cramps=muscle_cramps,
            nausea=nausea,
            confusion=confusion,
            simulation_batch_id=batch_id
        )
        
        records.append({
            "patient_name": patient_name,
            "age": age,
            "body_temp": body_temp,
            "water_intake": water_intake,
            "heat_index": heat_index,
            "predicted_risk": risk,
            "confidence": confidence
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
        "avg_heat_index": round(float(df_results["heat_index"].mean()), 2)
    }
    
    return summary
