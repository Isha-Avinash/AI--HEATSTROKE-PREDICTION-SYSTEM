FEATURE_LABELS = {
    "Age": "Age vulnerability",
    "BodyTemp": "Body temperature",
    "WaterIntake": "Hydration level",
    "Dizziness": "Dizziness",
    "Headache": "Headache",
    "HeartRate": "Heart rate",
    "OutdoorTemp": "Ambient temperature",
    "Humidity": "Humidity",
    "HeatIndex": "Apparent temperature",
    "MuscleCramps": "Muscle cramps",
    "Nausea": "Nausea/vomiting",
    "Confusion": "Confusion/delirium",
}


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def build_prediction_explanation(
    importances,
    age,
    body_temp,
    water_intake,
    dizziness,
    headache,
    heart_rate,
    outdoor_temp,
    humidity,
    heat_index,
    muscle_cramps,
    nausea,
    confusion,
):
    """
    Builds a lightweight local explanation by combining model feature importance
    with the current input's risk pressure.
    """
    risk_pressure = {
        "Age": 1.0 if int(age) <= 10 or int(age) >= 65 else 0.2 if int(age) <= 18 or int(age) >= 55 else 0.0,
        "BodyTemp": clamp((float(body_temp) - 37.5) / 3.5),
        "WaterIntake": clamp((2.5 - float(water_intake)) / 2.5),
        "Dizziness": float(bool(dizziness)),
        "Headache": float(bool(headache)),
        "HeartRate": clamp((int(heart_rate) - 90) / 50),
        "OutdoorTemp": clamp((float(outdoor_temp) - 30.0) / 16.0),
        "Humidity": clamp((float(humidity) - 55.0) / 40.0),
        "HeatIndex": clamp((float(heat_index) - 30.0) / 14.0),
        "MuscleCramps": float(bool(muscle_cramps)),
        "Nausea": float(bool(nausea)),
        "Confusion": float(bool(confusion)),
    }

    rows = []
    for feature, pressure in risk_pressure.items():
        model_weight = float(importances.get(feature, 0.0))
        influence = round(model_weight * pressure, 4)
        rows.append({
            "feature": feature,
            "label": FEATURE_LABELS.get(feature, feature),
            "model_weight": round(model_weight, 4),
            "risk_pressure": round(float(pressure), 3),
            "influence": influence,
        })

    rows = sorted(rows, key=lambda item: item["influence"], reverse=True)

    improvement_targets = []
    if body_temp >= 38.5:
        improvement_targets.append("Cool the body and reassess temperature after rest/cooling.")
    if water_intake < 2.0:
        improvement_targets.append("Improve hydration if the person is alert and not vomiting.")
    if heat_index >= 33.0:
        improvement_targets.append("Move to shade, air conditioning, or a lower-heat environment.")
    if heart_rate >= 110:
        improvement_targets.append("Stop exertion and monitor pulse during recovery.")
    if confusion:
        improvement_targets.append("Treat confusion as urgent; do not delay medical evaluation.")

    return {
        "heat_index": heat_index,
        "top_factors": [row for row in rows if row["influence"] > 0][:6],
        "all_factors": rows,
        "improvement_targets": improvement_targets[:5],
        "method_note": "Influence = trained feature importance x current risk pressure.",
    }
