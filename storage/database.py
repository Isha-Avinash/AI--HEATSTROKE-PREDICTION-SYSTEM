import sqlite3
import os
import csv
import json

DB_PATH = os.environ.get(
    "HEATSTROKE_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runtime", "heatstroke_records.db")
)

def init_db():
    """Initializes the database and creates/migrates local tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heatstroke_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            patient_name TEXT,
            age INTEGER,
            body_temp REAL,
            water_intake REAL,
            dizziness INTEGER,
            headache INTEGER,
            heart_rate INTEGER,
            outdoor_temp REAL,
            humidity REAL,
            heat_index REAL,
            calculated_bmi REAL,
            height_m REAL DEFAULT NULL,
            weight_kg REAL DEFAULT NULL,
            predicted_risk TEXT,
            confidence REAL,
            muscle_cramps INTEGER DEFAULT 0,
            nausea INTEGER DEFAULT 0,
            confusion INTEGER DEFAULT 0,
            simulation_batch_id TEXT DEFAULT NULL,
            ml_risk TEXT DEFAULT NULL,
            final_risk TEXT DEFAULT NULL,
            safety_override_applied INTEGER DEFAULT 0,
            safety_override_reasons TEXT DEFAULT NULL,
            model_type TEXT DEFAULT NULL,
            model_training_date TEXT DEFAULT NULL,
            model_accuracy REAL DEFAULT NULL,
            rule_engine_version TEXT DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT,
            actor TEXT DEFAULT 'system',
            entity_type TEXT,
            entity_id TEXT,
            details TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS followup_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            assessment_id INTEGER,
            patient_name TEXT,
            action_labels TEXT,
            notes TEXT,
            reassess_minutes INTEGER
        )
    """)
    
    # Run migrations to add columns if user has old db file
    columns_to_check = [
        ("muscle_cramps", "INTEGER DEFAULT 0"),
        ("nausea", "INTEGER DEFAULT 0"),
        ("confusion", "INTEGER DEFAULT 0"),
        ("simulation_batch_id", "TEXT DEFAULT NULL"),
        ("ml_risk", "TEXT DEFAULT NULL"),
        ("final_risk", "TEXT DEFAULT NULL"),
        ("safety_override_applied", "INTEGER DEFAULT 0"),
        ("safety_override_reasons", "TEXT DEFAULT NULL"),
        ("model_type", "TEXT DEFAULT NULL"),
        ("model_training_date", "TEXT DEFAULT NULL"),
        ("model_accuracy", "REAL DEFAULT NULL"),
        ("rule_engine_version", "TEXT DEFAULT NULL"),
        ("height_m", "REAL DEFAULT NULL"),
        ("weight_kg", "REAL DEFAULT NULL")
    ]
    for col_name, col_type in columns_to_check:
        try:
            cursor.execute(f"ALTER TABLE heatstroke_records ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
            
    conn.commit()
    conn.close()

def save_record(
    patient_name,
    age,
    body_temp,
    water_intake,
    dizziness,
    headache,
    heart_rate,
    outdoor_temp,
    humidity,
    heat_index,
    calculated_bmi,
    predicted_risk,
    confidence,
    height_m=None,
    weight_kg=None,
    muscle_cramps=0,
    nausea=0,
    confusion=0,
    simulation_batch_id=None,
    ml_risk=None,
    final_risk=None,
    safety_override_applied=0,
    safety_override_reasons=None,
    model_type=None,
    model_training_date=None,
    model_accuracy=None,
    rule_engine_version=None,
):
    """Saves a new patient risk prediction log to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    safety_reasons_json = json.dumps(safety_override_reasons or [])
    cursor.execute("""
        INSERT INTO heatstroke_records (
            patient_name, age, body_temp, water_intake, dizziness, headache, heart_rate,
            outdoor_temp, humidity, heat_index, calculated_bmi, height_m, weight_kg,
            predicted_risk, confidence,
            muscle_cramps, nausea, confusion, simulation_batch_id, ml_risk, final_risk,
            safety_override_applied, safety_override_reasons, model_type, model_training_date,
            model_accuracy, rule_engine_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        patient_name, age, body_temp, water_intake, dizziness, headache, heart_rate,
        outdoor_temp, humidity, heat_index, calculated_bmi, height_m, weight_kg,
        predicted_risk, confidence,
        muscle_cramps, nausea, confusion, simulation_batch_id, ml_risk, final_risk,
        int(bool(safety_override_applied)), safety_reasons_json, model_type, model_training_date,
        model_accuracy, rule_engine_version
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def log_audit_event(event_type, entity_type=None, entity_id=None, details=None, actor="system"):
    """Writes an audit event for demo traceability."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    details_json = json.dumps(details or {})
    cursor.execute("""
        INSERT INTO audit_log (event_type, actor, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?, ?)
    """, (event_type, actor, entity_type, str(entity_id) if entity_id is not None else None, details_json))
    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id

def get_audit_events(limit=100):
    """Returns recent audit events."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (int(limit),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_followup_actions(assessment_id, patient_name, action_labels, notes="", reassess_minutes=None):
    """Stores follow-up actions taken after an assessment."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO followup_actions (
            assessment_id, patient_name, action_labels, notes, reassess_minutes
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        assessment_id,
        patient_name,
        json.dumps(action_labels or []),
        notes or "",
        reassess_minutes,
    ))
    followup_id = cursor.lastrowid
    conn.commit()
    conn.close()
    log_audit_event(
        "followup_actions_recorded",
        entity_type="assessment",
        entity_id=assessment_id,
        details={
            "patient_name": patient_name,
            "actions": action_labels or [],
            "reassess_minutes": reassess_minutes,
        },
    )
    return followup_id

def get_recent_followups(limit=100):
    """Returns recent follow-up action records."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM followup_actions ORDER BY timestamp DESC LIMIT ?", (int(limit),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_records():
    """Retrieves all patient records sorted by timestamp descending."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM heatstroke_records ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_records_by_batch(batch_id):
    """Retrieves all records belonging to a specific simulation batch."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM heatstroke_records WHERE simulation_batch_id = ? ORDER BY timestamp ASC", (batch_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_records_by_batch(batch_id):
    """Deletes records for a specific batch id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM heatstroke_records WHERE simulation_batch_id = ?", (batch_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def load_demo_records(csv_path, batch_id="demo_client_seed"):
    """Loads demo records from CSV after replacing any previous demo seed batch."""
    delete_records_by_batch(batch_id)
    inserted = 0

    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            save_record(
                patient_name=row["patient_name"],
                age=int(row["age"]),
                body_temp=float(row["body_temp"]),
                water_intake=float(row["water_intake"]),
                dizziness=int(row["dizziness"]),
                headache=int(row["headache"]),
                heart_rate=int(row["heart_rate"]),
                outdoor_temp=float(row["outdoor_temp"]),
                humidity=float(row["humidity"]),
                heat_index=float(row["heat_index"]),
                calculated_bmi=float(row["calculated_bmi"]),
                predicted_risk=row["predicted_risk"],
                confidence=float(row["confidence"]),
                muscle_cramps=int(row["muscle_cramps"]),
                nausea=int(row["nausea"]),
                confusion=int(row["confusion"]),
                simulation_batch_id=batch_id,
                ml_risk=row["predicted_risk"],
                final_risk=row["predicted_risk"],
                safety_override_applied=0,
                safety_override_reasons=[],
                model_type="Demo Seed",
                model_training_date="N/A",
                model_accuracy=None,
                rule_engine_version="demo_seed",
            )
            inserted += 1

    log_audit_event(
        "demo_data_loaded",
        entity_type="batch",
        entity_id=batch_id,
        details={"csv_path": csv_path, "records_inserted": inserted},
    )
    return inserted

def clear_database():
    """Clears all logs from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM heatstroke_records")
    cursor.execute("DELETE FROM followup_actions")
    conn.commit()
    conn.close()
    log_audit_event("assessment_logs_cleared", entity_type="assessment")
