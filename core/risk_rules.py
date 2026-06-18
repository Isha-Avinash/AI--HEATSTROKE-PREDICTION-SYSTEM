RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
RISK_LABELS = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
RULE_ENGINE_VERSION = "safety_rules_v1.0"


def _higher_risk(current_risk, required_risk):
    current_score = RISK_ORDER.get(current_risk, 0)
    required_score = RISK_ORDER.get(required_risk, 0)
    return RISK_LABELS[max(current_score, required_score)]


def apply_safety_overrides(
    ml_risk,
    confidence,
    body_temp,
    heat_index,
    water_intake,
    heart_rate,
    dizziness,
    headache,
    muscle_cramps,
    nausea,
    confusion,
):
    """
    Applies conservative safety rules on top of the ML estimate.
    These rules make the final MVP demo safer and easier to explain.
    """
    final_risk = ml_risk
    override_reasons = []

    if body_temp >= 41.0:
        final_risk = _higher_risk(final_risk, "HIGH")
        override_reasons.append("Body temperature is 41.0 C or higher.")

    if confusion and body_temp >= 39.5:
        final_risk = _higher_risk(final_risk, "HIGH")
        override_reasons.append("Confusion with elevated body temperature is an emergency red flag.")

    if heat_index >= 41.0 and (dizziness or nausea or muscle_cramps or headache):
        final_risk = _higher_risk(final_risk, "HIGH")
        override_reasons.append("Extreme heat index plus active symptoms requires urgent attention.")

    if body_temp >= 39.0 and heart_rate >= 120 and water_intake < 1.5:
        final_risk = _higher_risk(final_risk, "HIGH")
        override_reasons.append("High body temperature, tachycardia, and low hydration are clustered risk signals.")

    if heat_index >= 33.0 and (dizziness or nausea or muscle_cramps):
        final_risk = _higher_risk(final_risk, "MEDIUM")
        override_reasons.append("Hot conditions with heat-illness symptoms should be treated as at least moderate risk.")

    if body_temp >= 38.5 and water_intake < 1.0:
        final_risk = _higher_risk(final_risk, "MEDIUM")
        override_reasons.append("Elevated body temperature with very low hydration should be treated as at least moderate risk.")

    return {
        "ml_risk": ml_risk,
        "final_risk": final_risk,
        "confidence": confidence,
        "override_applied": final_risk != ml_risk,
        "override_reasons": override_reasons,
        "rule_engine_version": RULE_ENGINE_VERSION,
    }
