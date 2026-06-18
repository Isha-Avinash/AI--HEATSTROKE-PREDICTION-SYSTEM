import joblib
import os
import pandas as pd
from core.explainability import build_prediction_explanation
from services.training_service import train_and_save_model, calculate_heat_index

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_ROOT, "artifacts", "models", "heatstroke_model.joblib")

def get_model():
    """Loads the model, auto-training it if it doesn't exist."""
    if not os.path.exists(MODEL_PATH):
        print("Model file not found. Auto-training classifier...")
        train_and_save_model()
    return joblib.load(MODEL_PATH)

def predict_risk_ml(age, body_temp, water_intake, dizziness, headache, heart_rate, outdoor_temp, humidity, muscle_cramps, nausea, confusion):
    """
    Predicts the risk of heatstroke using the local trained ML classifier.
    Returns a dict with prediction string (LOW, MEDIUM, HIGH) and confidence probability.
    """
    model_data = get_model()
    clf = model_data["model"]
    
    # Calculate heat index
    heat_index = calculate_heat_index(outdoor_temp, humidity)
    
    # Construct input dataframe matching exact feature order
    # features: ["Age", "BodyTemp", "WaterIntake", "Dizziness", "Headache", "HeartRate", "OutdoorTemp", "Humidity", "HeatIndex", "MuscleCramps", "Nausea", "Confusion"]
    input_data = pd.DataFrame([{
        "Age": int(age),
        "BodyTemp": float(body_temp),
        "WaterIntake": float(water_intake),
        "Dizziness": int(dizziness),
        "Headache": int(headache),
        "HeartRate": int(heart_rate),
        "OutdoorTemp": float(outdoor_temp),
        "Humidity": float(humidity),
        "HeatIndex": float(heat_index),
        "MuscleCramps": int(muscle_cramps),
        "Nausea": int(nausea),
        "Confusion": int(confusion)
    }])
    
    # Predict
    pred = clf.predict(input_data)[0]
    prob = clf.predict_proba(input_data)[0]
    
    # Map predictions back to labels
    risk_labels = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
    predicted_risk = risk_labels[pred]
    confidence = prob[pred] * 100
    
    return {
        "predicted_risk": predicted_risk,
        "confidence": round(confidence, 1),
        "heat_index": heat_index,
        "probabilities": {risk_labels[i]: round(prob[i] * 100, 1) for i in range(len(prob))}
    }

def explain_prediction_ml(age, body_temp, water_intake, dizziness, headache, heart_rate, outdoor_temp, humidity, muscle_cramps, nausea, confusion):
    """
    Builds a lightweight local explanation for the current prediction input.
    """
    model_data = get_model()
    importances = model_data.get("feature_importances", {})
    heat_index = calculate_heat_index(outdoor_temp, humidity)
    return build_prediction_explanation(
        importances=importances,
        age=age,
        body_temp=body_temp,
        water_intake=water_intake,
        dizziness=dizziness,
        headache=headache,
        heart_rate=heart_rate,
        outdoor_temp=outdoor_temp,
        humidity=humidity,
        heat_index=heat_index,
        muscle_cramps=muscle_cramps,
        nausea=nausea,
        confusion=confusion,
    )

def get_feature_importances():
    """Returns the model's feature importances dict."""
    model_data = get_model()
    return model_data.get("feature_importances", {})

def get_model_metadata():
    """Returns model metrics, type, and training date."""
    model_data = get_model()
    return {
        "model_type": model_data.get("model_type", "RandomForest"),
        "metrics": model_data.get("metrics", {}),
        "training_date": model_data.get("training_date", "N/A")
    }

def get_confusion_matrix():
    """Returns the serialized confusion matrix array."""
    model_data = get_model()
    return model_data.get("confusion_matrix", None)
