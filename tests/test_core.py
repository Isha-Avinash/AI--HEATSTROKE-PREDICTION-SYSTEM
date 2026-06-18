import os
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from storage import database
from storage.database import load_demo_records
from services.model_service import explain_prediction_ml, predict_risk_ml
from services.training_service import calculate_heat_index
from core.risk_rules import apply_safety_overrides
from services.simulation_service import get_scenario_profile, run_cohort_simulation
from services.symptom_service import extract_symptoms_keyword
from services.workflow_service import build_patient_profile, calculate_triage_priority
from services.risk_tracker_service import get_patient_timeline


class HeatstrokeCoreTests(unittest.TestCase):
    def test_heat_index_increases_with_humidity(self):
        dry = calculate_heat_index(35.0, 25.0)
        humid = calculate_heat_index(35.0, 80.0)
        self.assertGreater(humid, dry)

    def test_prediction_and_explanation_shape(self):
        prediction = predict_risk_ml(
            age=35,
            body_temp=39.5,
            water_intake=1.0,
            dizziness=1,
            headache=1,
            heart_rate=125,
            outdoor_temp=42.0,
            humidity=35.0,
            muscle_cramps=1,
            nausea=1,
            confusion=0,
        )
        self.assertIn(prediction["predicted_risk"], {"LOW", "MEDIUM", "HIGH"})
        self.assertIn("HIGH", prediction["probabilities"])

        explanation = explain_prediction_ml(
            age=35,
            body_temp=39.5,
            water_intake=1.0,
            dizziness=1,
            headache=1,
            heart_rate=125,
            outdoor_temp=42.0,
            humidity=35.0,
            muscle_cramps=1,
            nausea=1,
            confusion=0,
        )
        self.assertGreater(len(explanation["all_factors"]), 0)
        self.assertIn("method_note", explanation)

    def test_keyword_symptom_parser_common_terms(self):
        result = extract_symptoms_keyword("I feel dizzy, nauseous, confused, and my head hurts.")
        self.assertEqual(result["flags"]["Dizziness"], 1)
        self.assertEqual(result["flags"]["Nausea"], 1)
        self.assertEqual(result["flags"]["Confusion"], 1)
        self.assertEqual(result["flags"]["Headache"], 1)

    def test_database_round_trip_with_temp_db(self):
        original_path = database.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "records.db")
            database.init_db()
            database.save_record(
                patient_name="Test Patient",
                age=30,
                body_temp=37.5,
                water_intake=2.5,
                dizziness=0,
                headache=0,
                heart_rate=80,
                outdoor_temp=32.0,
                humidity=55.0,
                heat_index=35.0,
                calculated_bmi=22.0,
                predicted_risk="LOW",
                confidence=92.5,
                ml_risk="LOW",
                final_risk="LOW",
                model_type="UnitModel",
                model_training_date="2026-06-15 10:00:00",
                model_accuracy=91.2,
                rule_engine_version="test_rules_v1",
            )
            rows = database.get_all_records()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["patient_name"], "Test Patient")
            self.assertEqual(rows[0]["ml_risk"], "LOW")
            self.assertEqual(rows[0]["final_risk"], "LOW")
            self.assertEqual(rows[0]["model_type"], "UnitModel")
            event_id = database.log_audit_event(
                "unit_test_event",
                entity_type="assessment",
                entity_id=rows[0]["id"],
                details={"final_risk": "LOW"},
            )
            events = database.get_audit_events()
            self.assertEqual(events[0]["id"], event_id)
            self.assertEqual(events[0]["event_type"], "unit_test_event")
        database.DB_PATH = original_path

    def test_followup_actions_round_trip(self):
        original_path = database.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "followups.db")
            database.init_db()
            assessment_id = database.save_record(
                patient_name="Follow Up Patient",
                age=31,
                body_temp=39.0,
                water_intake=1.0,
                dizziness=1,
                headache=1,
                heart_rate=118,
                outdoor_temp=40.0,
                humidity=50.0,
                heat_index=45.0,
                calculated_bmi=23.0,
                predicted_risk="MEDIUM",
                confidence=82.0,
                ml_risk="MEDIUM",
                final_risk="MEDIUM",
            )
            followup_id = database.save_followup_actions(
                assessment_id,
                "Follow Up Patient",
                ["Move to cooler area", "Reassess in 15 minutes"],
                notes="Cooling started.",
                reassess_minutes=15,
            )
            rows = database.get_recent_followups()
            self.assertEqual(rows[0]["id"], followup_id)
            self.assertEqual(rows[0]["assessment_id"], assessment_id)
            self.assertIn("Move to cooler area", rows[0]["action_labels"])
        database.DB_PATH = original_path

    def test_patient_timeline_matches_name_case_and_spaces(self):
        original_path = database.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "timeline.db")
            database.init_db()
            database.save_record(
                patient_name="Aditi",
                age=28,
                body_temp=37.0,
                water_intake=2.0,
                dizziness=1,
                headache=0,
                heart_rate=80,
                outdoor_temp=35.0,
                humidity=50.0,
                heat_index=40.7,
                calculated_bmi=22.86,
                predicted_risk="MEDIUM",
                confidence=65.9,
                height_m=1.75,
                weight_kg=70.0,
                ml_risk="MEDIUM",
                final_risk="MEDIUM",
            )
            rows = get_patient_timeline("  aditi  ", age=28, height_m=1.75)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["patient_name"], "Aditi")
            self.assertEqual(rows[0]["height_m"], 1.75)
            self.assertEqual(get_patient_timeline("aditi", age=29, height_m=1.75), [])
            self.assertEqual(get_patient_timeline("aditi", age=28, height_m=1.70), [])
        database.DB_PATH = original_path

    def test_demo_loader_replaces_seed_batch(self):
        original_path = database.DB_PATH
        demo_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demo_data", "sample_assessments.csv")
        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "demo.db")
            database.init_db()
            first_count = load_demo_records(demo_csv)
            second_count = load_demo_records(demo_csv)
            rows = database.get_records_by_batch("demo_client_seed")
            self.assertEqual(first_count, second_count)
            self.assertEqual(len(rows), second_count)
            self.assertGreater(second_count, 0)
        database.DB_PATH = original_path

    def test_safety_override_escalates_red_flags(self):
        result = apply_safety_overrides(
            ml_risk="MEDIUM",
            confidence=81.0,
            body_temp=40.0,
            heat_index=42.0,
            water_intake=0.8,
            heart_rate=130,
            dizziness=1,
            headache=1,
            muscle_cramps=0,
            nausea=1,
            confusion=1,
        )
        self.assertEqual(result["final_risk"], "HIGH")
        self.assertTrue(result["override_applied"])
        self.assertGreater(len(result["override_reasons"]), 0)
        self.assertIn("rule_engine_version", result)

    def test_safety_override_keeps_low_when_no_red_flags(self):
        result = apply_safety_overrides(
            ml_risk="LOW",
            confidence=94.0,
            body_temp=37.1,
            heat_index=30.0,
            water_intake=2.6,
            heart_rate=82,
            dizziness=0,
            headache=0,
            muscle_cramps=0,
            nausea=0,
            confusion=0,
        )
        self.assertEqual(result["final_risk"], "LOW")
        self.assertFalse(result["override_applied"])
        self.assertEqual(result["override_reasons"], [])

    def test_safety_override_body_temp_critical(self):
        result = apply_safety_overrides(
            ml_risk="LOW",
            confidence=70.0,
            body_temp=41.2,
            heat_index=32.0,
            water_intake=2.0,
            heart_rate=100,
            dizziness=0,
            headache=0,
            muscle_cramps=0,
            nausea=0,
            confusion=0,
        )
        self.assertEqual(result["final_risk"], "HIGH")
        self.assertTrue(result["override_applied"])

    def test_patient_memory_and_triage_priority(self):
        timeline = [
            {
                "timestamp": "2026-06-16 10:00:00",
                "patient_name": "Asha",
                "predicted_risk": "LOW",
                "body_temp": 37.0,
                "water_intake": 2.4,
                "dizziness": 1,
                "headache": 0,
                "muscle_cramps": 0,
                "nausea": 0,
                "confusion": 0,
                "heart_rate": 85,
                "heat_index": 32.0,
            },
            {
                "timestamp": "2026-06-16 10:20:00",
                "patient_name": "Asha",
                "predicted_risk": "HIGH",
                "body_temp": 40.1,
                "water_intake": 0.8,
                "dizziness": 1,
                "headache": 1,
                "muscle_cramps": 0,
                "nausea": 0,
                "confusion": 1,
                "heart_rate": 128,
                "heat_index": 44.0,
                "safety_override_applied": 1,
            },
        ]
        profile = build_patient_profile(timeline)
        triage = calculate_triage_priority(timeline[-1], timeline)
        self.assertEqual(profile["assessment_count"], 2)
        self.assertIn("dizziness", profile["repeated_symptoms"])
        self.assertEqual(triage["priority"], "Critical")
        self.assertTrue(triage["needs_reassessment"])

    def test_custom_simulation_profile(self):
        original_path = database.DB_PATH
        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "sim.db")
            database.init_db()
            profile = get_scenario_profile("Normal Bangalore")
            summary = run_cohort_simulation(5, "Unit Test Scenario", profile)
            self.assertEqual(summary["total_simulated"], 5)
            self.assertEqual(len(summary["records"]), 5)
            self.assertEqual(sum(summary["risk_counts"].values()), 5)
            self.assertFalse(pd.DataFrame(summary["records"]).empty)
        database.DB_PATH = original_path

    def test_simulation_applies_safety_overrides(self):
        original_path = database.DB_PATH
        profile = {
            "outdoor_temp": (30.0, 30.0),
            "humidity": (40.0, 40.0),
            "water_intake": (2.0, 2.0),
            "body_temp": (41.2, 41.2),
            "heart_rate": (90, 91),
            "symptoms": {
                "dizziness": 0.0,
                "headache": 0.0,
                "muscle_cramps": 0.0,
                "nausea": 0.0,
                "confusion": 0.0,
            },
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            database.DB_PATH = os.path.join(tmpdir, "sim_override.db")
            database.init_db()
            with patch(
                "services.simulation_service.predict_risk_ml",
                return_value={
                    "predicted_risk": "LOW",
                    "confidence": 88.0,
                    "heat_index": calculate_heat_index(30.0, 40.0),
                    "probabilities": {"LOW": 88.0, "MEDIUM": 10.0, "HIGH": 2.0},
                },
            ):
                summary = run_cohort_simulation(1, "Override Test", profile)

            self.assertEqual(summary["risk_counts"]["HIGH"], 1)
            self.assertEqual(summary["records"][0]["ml_risk"], "LOW")
            self.assertEqual(summary["records"][0]["final_risk"], "HIGH")
            self.assertTrue(summary["records"][0]["safety_override_applied"])

            rows = database.get_records_by_batch(summary["batch_id"])
            self.assertEqual(rows[0]["ml_risk"], "LOW")
            self.assertEqual(rows[0]["final_risk"], "HIGH")
            self.assertEqual(rows[0]["safety_override_applied"], 1)
        database.DB_PATH = original_path

    def test_simulation_random_seed_reproduces_records(self):
        original_path = database.DB_PATH
        profile = get_scenario_profile("Monsoon Mumbai")
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "services.simulation_service.predict_risk_ml",
                return_value={
                    "predicted_risk": "MEDIUM",
                    "confidence": 77.0,
                    "heat_index": 40.0,
                    "probabilities": {"LOW": 10.0, "MEDIUM": 77.0, "HIGH": 13.0},
                },
            ):
                database.DB_PATH = os.path.join(tmpdir, "seed_a.db")
                database.init_db()
                first = run_cohort_simulation(4, "Seed Test", profile, random_seed=1234)

                database.DB_PATH = os.path.join(tmpdir, "seed_b.db")
                database.init_db()
                second = run_cohort_simulation(4, "Seed Test", profile, random_seed=1234)

            compare_cols = [
                "age", "outdoor_temp", "humidity", "body_temp", "water_intake",
                "heart_rate", "dizziness", "headache", "muscle_cramps",
                "nausea", "confusion", "predicted_risk"
            ]
            first_records = [{col: record[col] for col in compare_cols} for record in first["records"]]
            second_records = [{col: record[col] for col in compare_cols} for record in second["records"]]
            self.assertEqual(first["random_seed"], 1234)
            self.assertEqual(first_records, second_records)
        database.DB_PATH = original_path


if __name__ == "__main__":
    unittest.main()
