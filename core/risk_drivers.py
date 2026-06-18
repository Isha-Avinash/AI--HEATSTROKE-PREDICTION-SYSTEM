def get_risk_drivers(body_temp, water_intake, heart_rate, heat_index, symptoms):
    """Builds explainable, rule-based drivers for the screening result."""
    drivers = []
    protective = []

    if body_temp >= 40.0:
        drivers.append(("Critical body temperature", f"{body_temp:.1f} C is at/near heatstroke concern range."))
    elif body_temp >= 38.5:
        drivers.append(("Elevated body temperature", f"{body_temp:.1f} C suggests heat strain."))
    else:
        protective.append(("Body temperature", f"{body_temp:.1f} C is not elevated."))

    if heat_index >= 41.0:
        drivers.append(("Extreme apparent heat", f"Heat index is {heat_index:.1f} C."))
    elif heat_index >= 33.0:
        drivers.append(("Hot environment", f"Heat index is {heat_index:.1f} C."))
    else:
        protective.append(("Environment", f"Heat index is {heat_index:.1f} C."))

    if water_intake < 1.0:
        drivers.append(("Very low hydration", f"Only {water_intake:.1f} L logged today."))
    elif water_intake < 2.0:
        drivers.append(("Below-target hydration", f"{water_intake:.1f} L may be low during heat exposure."))
    else:
        protective.append(("Hydration", f"{water_intake:.1f} L logged today."))

    if heart_rate >= 120:
        drivers.append(("High heart rate", f"{heart_rate} bpm indicates cardiovascular strain."))
    elif heart_rate >= 100:
        drivers.append(("Raised heart rate", f"{heart_rate} bpm may reflect heat stress or exertion."))

    symptom_labels = {
        "dizziness": "Dizziness",
        "headache": "Headache",
        "muscle_cramps": "Muscle cramps",
        "nausea": "Nausea/vomiting",
        "confusion": "Confusion/delirium",
    }
    active_symptoms = [label for key, label in symptom_labels.items() if symptoms.get(key)]
    if active_symptoms:
        drivers.append(("Active symptoms", ", ".join(active_symptoms)))
    else:
        protective.append(("Symptoms", "No tracked symptoms selected."))

    if symptoms.get("confusion"):
        drivers.insert(0, ("Neurological warning sign", "Confusion is a red-flag symptom in heat illness."))

    return {
        "drivers": drivers[:5],
        "protective": protective[:3],
    }
