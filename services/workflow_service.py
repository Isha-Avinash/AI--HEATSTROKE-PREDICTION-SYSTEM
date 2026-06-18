from datetime import datetime


RISK_SCORE = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def _parse_timestamp(value):
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def build_patient_profile(timeline):
    """Builds memory-style patient context from prior assessments."""
    if not timeline:
        return {
            "assessment_count": 0,
            "baseline_body_temp": None,
            "baseline_hydration": None,
            "latest": None,
            "repeated_symptoms": [],
            "summary": "No prior patient memory is available yet.",
        }

    sorted_timeline = sorted(timeline, key=lambda row: str(row.get("timestamp", "")))
    latest = sorted_timeline[-1]
    baseline_window = sorted_timeline[:-1] or sorted_timeline
    baseline_body_temp = round(
        sum(float(row.get("body_temp", 0.0)) for row in baseline_window) / len(baseline_window),
        2,
    )
    baseline_hydration = round(
        sum(float(row.get("water_intake", 0.0)) for row in baseline_window) / len(baseline_window),
        2,
    )

    symptom_cols = ["dizziness", "headache", "muscle_cramps", "nausea", "confusion"]
    symptom_labels = {
        "dizziness": "dizziness",
        "headache": "headache",
        "muscle_cramps": "muscle cramps",
        "nausea": "nausea",
        "confusion": "confusion",
    }
    repeated_symptoms = []
    if len(sorted_timeline) >= 2:
        recent = sorted_timeline[-3:]
        for symptom in symptom_cols:
            if sum(int(row.get(symptom, 0) or 0) for row in recent) >= 2:
                repeated_symptoms.append(symptom_labels[symptom])

    temp_delta = float(latest.get("body_temp", 0.0)) - baseline_body_temp
    hydration_delta = float(latest.get("water_intake", 0.0)) - baseline_hydration
    summary_parts = [f"{len(sorted_timeline)} prior assessment(s) found."]
    if len(sorted_timeline) >= 2:
        summary_parts.append(f"Latest body temp is {temp_delta:+.1f} C vs baseline.")
        summary_parts.append(f"Hydration is {hydration_delta:+.1f} L vs baseline.")
    if repeated_symptoms:
        summary_parts.append("Repeated symptoms: " + ", ".join(repeated_symptoms) + ".")

    return {
        "assessment_count": len(sorted_timeline),
        "baseline_body_temp": baseline_body_temp,
        "baseline_hydration": baseline_hydration,
        "latest": latest,
        "repeated_symptoms": repeated_symptoms,
        "summary": " ".join(summary_parts),
    }


def get_followup_actions(risk):
    """Returns operational follow-up actions for the selected risk level."""
    actions = {
        "LOW": [
            "Continue hydration monitoring",
            "Repeat screening if symptoms appear",
        ],
        "MEDIUM": [
            "Move to a cooler area",
            "Give water or electrolytes if alert",
            "Pause exertion",
            "Reassess in 15 minutes",
        ],
        "HIGH": [
            "Start active cooling",
            "Move to shade or air conditioning",
            "Call emergency care if confusion, collapse, or very high temperature is present",
            "Reassess in 5 minutes",
            "Do not force fluids if confused or vomiting",
        ],
    }
    return actions.get(risk, actions["LOW"])


def calculate_triage_priority(record, timeline=None, now=None):
    """Scores assessment urgency using risk, red flags, trend, and follow-up timing."""
    risk = record.get("predicted_risk") or record.get("final_risk") or "LOW"
    score = RISK_SCORE.get(risk, 0) * 30
    reasons = []

    if risk == "HIGH":
        reasons.append("High final risk")
    elif risk == "MEDIUM":
        reasons.append("Moderate final risk")

    if int(record.get("confusion", 0) or 0):
        score += 35
        reasons.append("Confusion red flag")
    if float(record.get("body_temp", 0.0) or 0.0) >= 40.0:
        score += 30
        reasons.append("Very high body temperature")
    elif float(record.get("body_temp", 0.0) or 0.0) >= 39.0:
        score += 15
        reasons.append("Elevated body temperature")
    if float(record.get("heat_index", 0.0) or 0.0) >= 41.0:
        score += 15
        reasons.append("Extreme heat index")
    if float(record.get("water_intake", 0.0) or 0.0) < 1.0:
        score += 10
        reasons.append("Very low hydration")
    if int(record.get("safety_override_applied", 0) or 0):
        score += 15
        reasons.append("Safety override applied")

    if timeline and len(timeline) >= 2:
        latest_two = sorted(timeline, key=lambda row: str(row.get("timestamp", "")))[-2:]
        previous_risk = RISK_SCORE.get(latest_two[0].get("predicted_risk", "LOW"), 0)
        current_risk = RISK_SCORE.get(latest_two[1].get("predicted_risk", "LOW"), 0)
        if current_risk > previous_risk:
            score += 20
            reasons.append("Risk is rising")
        if float(latest_two[1].get("body_temp", 0.0)) - float(latest_two[0].get("body_temp", 0.0)) >= 0.3:
            score += 10
            reasons.append("Body temperature is rising")

    timestamp = _parse_timestamp(record.get("timestamp"))
    minutes_since = None
    if timestamp:
        current_time = now or datetime.now()
        minutes_since = max(0, int((current_time - timestamp.replace(tzinfo=None)).total_seconds() // 60))
        if risk == "HIGH" and minutes_since >= 5:
            score += 15
            reasons.append("High-risk reassessment window reached")
        elif risk == "MEDIUM" and minutes_since >= 15:
            score += 10
            reasons.append("Moderate-risk reassessment window reached")

    if score >= 85:
        priority = "Critical"
    elif score >= 55:
        priority = "High"
    elif score >= 25:
        priority = "Watch"
    else:
        priority = "Routine"

    needs_reassessment = (
        risk == "HIGH"
        or int(record.get("confusion", 0) or 0) == 1
        or float(record.get("body_temp", 0.0) or 0.0) >= 39.5
        or "reassessment window reached" in " ".join(reasons).lower()
    )

    return {
        "score": min(score, 100),
        "priority": priority,
        "needs_reassessment": needs_reassessment,
        "minutes_since": minutes_since,
        "reasons": reasons or ["No urgent signals"],
    }


def build_reassessment_prefill(record):
    """Returns Streamlit session-state values for reassessing a previous patient."""
    height = 1.75
    bmi = float(record.get("calculated_bmi", 22.0) or 22.0)
    weight = round(bmi * (height ** 2), 1)
    return {
        "patient_name_input": record.get("patient_name", "Anonymous"),
        "age_input": int(record.get("age", 28) or 28),
        "weight_input": float(weight),
        "height_input": float(height),
        "heart_rate_input": int(record.get("heart_rate", 80) or 80),
        "body_temp_input": float(record.get("body_temp", 37.0) or 37.0),
        "water_intake_input": float(record.get("water_intake", 2.0) or 2.0),
        "temp": float(record.get("outdoor_temp", 35.0) or 35.0),
        "humidity": float(record.get("humidity", 50.0) or 50.0),
        "symptom_dizziness": bool(record.get("dizziness", 0)),
        "symptom_headache": bool(record.get("headache", 0)),
        "symptom_cramps": bool(record.get("muscle_cramps", 0)),
        "symptom_nausea": bool(record.get("nausea", 0)),
        "symptom_confusion": bool(record.get("confusion", 0)),
    }
