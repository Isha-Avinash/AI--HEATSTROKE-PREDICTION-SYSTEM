import sqlite3
import storage.database as database

def get_patient_timeline(patient_name, age=None, height_m=None):
    """
    Retrieves chronological diagnostic history for a specific patient.
    """
    normalized_name = (patient_name or "").strip()
    if normalized_name == "" or normalized_name.casefold() == "anonymous":
        return []
        
    conn = sqlite3.connect(database.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    conditions = ["lower(trim(patient_name)) = lower(trim(?))"]
    params = [normalized_name]
    if age is not None:
        conditions.append("age = ?")
        params.append(int(age))
    if height_m is not None:
        conditions.append("(height_m IS NULL OR abs(height_m - ?) <= 0.01)")
        params.append(float(height_m))

    cursor.execute(
        f"""
        SELECT *
        FROM heatstroke_records
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp ASC
        """,
        params
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def detect_risk_trend(timeline):
    """
    Analyzes patient records to detect escalation trends.
    Returns a dict with trend flags and clinical warnings.
    """
    if len(timeline) < 2:
        return {
            "status": "Stable",
            "message": "Insufficient history to establish trend (requires 2+ assessments).",
            "escalating": False,
            "temp_rising": False,
            "risk_velocity": 0.0
        }
        
    # Map risks to numeric values
    risk_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    
    last_records = timeline[-3:]  # Analyse up to last 3 records
    
    risks = [risk_map.get(r["predicted_risk"], 0) for r in last_records]
    temps = [r["body_temp"] for r in last_records]
    
    escalating = False
    temp_rising = False
    
    # 1. Check risk escalation (e.g. LOW -> MEDIUM or MEDIUM -> HIGH)
    if len(risks) >= 2:
        if risks[-1] > risks[0]:
            escalating = True
            
    # 2. Check temp rising (e.g. increase of 0.5C or more in the window)
    if len(temps) >= 2:
        if temps[-1] > temps[0] and (temps[-1] - temps[0]) >= 0.3:
            temp_rising = True
            
    # 3. Compute risk velocity (change in risk per assessment in the window)
    risk_velocity = 0.0
    if len(risks) >= 2:
        risk_velocity = (risks[-1] - risks[0]) / (len(risks) - 1)
        
    # Formatting warning alerts
    if escalating and temp_rising:
        status = "CRITICAL ESCALATION"
        message = "🚨 Worsening Trend: Risk category and body temperature are both rising!"
    elif escalating:
        status = "RISK ESCALATING"
        message = "⚠️ Warning: Patient risk category is rising over consecutive assessments."
    elif temp_rising:
        status = "TEMP RISING"
        message = "🌡️ Warning: Patient body temperature is trending upwards."
    else:
        status = "Stable"
        message = "✅ Patient parameters appear stable."
        
    return {
        "status": status,
        "message": message,
        "escalating": escalating,
        "temp_rising": temp_rising,
        "risk_velocity": risk_velocity
    }
