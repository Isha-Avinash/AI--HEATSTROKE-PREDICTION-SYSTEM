from core.risk_rules import apply_safety_overrides
from core.risk_drivers import get_risk_drivers
from services.model_service import explain_prediction_ml, get_model_metadata, predict_risk_ml


def run_screening(
    age,
    body_temp,
    water_intake,
    dizziness,
    headache,
    heart_rate,
    outdoor_temp,
    humidity,
    muscle_cramps,
    nausea,
    confusion,
):
    """Coordinates model prediction, safety overrides, and explanation data."""
    ml_result = predict_risk_ml(
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
        confusion=confusion,
    )
    model_metadata = get_model_metadata()
    metrics = model_metadata.get("metrics", {})

    safety_result = apply_safety_overrides(
        ml_risk=ml_result["predicted_risk"],
        confidence=ml_result["confidence"],
        body_temp=body_temp,
        heat_index=ml_result["heat_index"],
        water_intake=water_intake,
        heart_rate=heart_rate,
        dizziness=dizziness,
        headache=headache,
        muscle_cramps=muscle_cramps,
        nausea=nausea,
        confusion=confusion,
    )

    symptoms = {
        "dizziness": dizziness,
        "headache": headache,
        "muscle_cramps": muscle_cramps,
        "nausea": nausea,
        "confusion": confusion,
    }

    risk_drivers = get_risk_drivers(
        body_temp=body_temp,
        water_intake=water_intake,
        heart_rate=heart_rate,
        heat_index=ml_result["heat_index"],
        symptoms=symptoms,
    )

    model_explanation = explain_prediction_ml(
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
        confusion=confusion,
    )

    return {
        "ml_result": ml_result,
        "safety_result": safety_result,
        "final_risk": safety_result["final_risk"],
        "risk_drivers": risk_drivers,
        "model_explanation": model_explanation,
        "model_metadata": {
            "model_type": model_metadata.get("model_type", "N/A"),
            "training_date": model_metadata.get("training_date", "N/A"),
            "accuracy": metrics.get("accuracy"),
        },
    }
