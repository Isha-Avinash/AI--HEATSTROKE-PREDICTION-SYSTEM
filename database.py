import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heatstroke_records.db")

def init_db():
    """Initializes the database and creates/migrates the heatstroke_records table."""
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
            predicted_risk TEXT,
            confidence REAL,
            muscle_cramps INTEGER DEFAULT 0,
            nausea INTEGER DEFAULT 0,
            confusion INTEGER DEFAULT 0,
            simulation_batch_id TEXT DEFAULT NULL
        )
    """)
    
    # Run migrations to add columns if user has old db file
    columns_to_check = [
        ("muscle_cramps", "INTEGER DEFAULT 0"),
        ("nausea", "INTEGER DEFAULT 0"),
        ("confusion", "INTEGER DEFAULT 0"),
        ("simulation_batch_id", "TEXT DEFAULT NULL")
    ]
    for col_name, col_type in columns_to_check:
        try:
            cursor.execute(f"ALTER TABLE heatstroke_records ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
            
    conn.commit()
    conn.close()

def save_record(patient_name, age, body_temp, water_intake, dizziness, headache, heart_rate, outdoor_temp, humidity, heat_index, calculated_bmi, predicted_risk, confidence, muscle_cramps=0, nausea=0, confusion=0, simulation_batch_id=None):
    """Saves a new patient risk prediction log to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO heatstroke_records (
            patient_name, age, body_temp, water_intake, dizziness, headache, heart_rate, outdoor_temp, humidity, heat_index, calculated_bmi, predicted_risk, confidence, muscle_cramps, nausea, confusion, simulation_batch_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (patient_name, age, body_temp, water_intake, dizziness, headache, heart_rate, outdoor_temp, humidity, heat_index, calculated_bmi, predicted_risk, confidence, muscle_cramps, nausea, confusion, simulation_batch_id))
    conn.commit()
    conn.close()

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

def clear_database():
    """Clears all logs from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM heatstroke_records")
    conn.commit()
    conn.close()
