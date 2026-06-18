import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime

# Import project modules
from storage.database import init_db, save_record, get_all_records, get_records_by_batch, get_audit_events, log_audit_event, save_followup_actions, get_recent_followups
from services.model_service import get_feature_importances, get_confusion_matrix
from services.weather_service import get_live_weather
from services.training_service import calculate_heat_index
from views.ui_helpers import (
    inject_custom_css,
    speak_browser,
    get_health_recommendations,
    render_emergency_checklist,
    render_model_explanation_panel,
    render_nlp_review_panel,
    render_result_overview,
    render_risk_driver_panel,
)
from services.symptom_service import extract_symptoms
from services.risk_tracker_service import get_patient_timeline, detect_risk_trend
from services.prediction_service import run_screening
from services.simulation_service import get_scenario_profile, run_cohort_simulation
from services.workflow_service import (
    build_patient_profile,
    build_reassessment_prefill,
    calculate_triage_priority,
    get_followup_actions,
)
from views.header import render_app_header
from views.safety_protocols import render_safety_protocols
from views.sidebar import render_sidebar

# Initialize DB on load
init_db()

# Streamlit App Configurations
st.set_page_config(
    page_title="Heat Stress Risk Screening Demo",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject modern Custom CSS definitions
inject_custom_css()

render_sidebar()

render_app_header()

pending_reassessment = st.session_state.pop("pending_reassessment_prefill", None)
if pending_reassessment:
    for key, value in pending_reassessment.items():
        st.session_state[key] = value
    st.session_state.reassessment_context = st.session_state.pop(
        "pending_reassessment_context",
        "Reassessment fields are ready.",
    )

# Define Tabs
tab_pred, tab_analytics, tab_sim, tab_guide = st.tabs([
    "Live Screening", 
    "Monitoring Dashboard", 
    "Scenario Simulator",
    "Safety Protocols"
])


def render_followup_panel(final_risk, assessment_id, patient_name):
    """Renders and persists risk-aware follow-up actions."""
    followup_panel = (
        st.expander("Optional follow-up", expanded=False)
        if final_risk == "LOW"
        else st.container(border=True)
    )
    with followup_panel:
        followup_heading = "Optional follow-up" if final_risk == "LOW" else "Response actions"
        st.markdown(f"<h4>{followup_heading}</h4>", unsafe_allow_html=True)
        if final_risk == "HIGH":
            st.error("High-risk result: record urgent response steps and reassess soon.")
        elif final_risk == "MEDIUM":
            st.warning("Moderate-risk result: record cooling/hydration steps and plan reassessment.")
        else:
            st.caption("Optional: record routine monitoring steps for this stable screening.")

        suggested_actions = get_followup_actions(final_risk)
        selected_actions = []
        for idx, action in enumerate(suggested_actions):
            if st.checkbox(action, value=final_risk in {"MEDIUM", "HIGH"}, key=f"followup_action_{assessment_id}_{idx}"):
                selected_actions.append(action)

        default_reassess = 5 if final_risk == "HIGH" else 15 if final_risk == "MEDIUM" else 60
        reassess_minutes = st.number_input(
            "Optional reassessment in minutes" if final_risk == "LOW" else "Reassess in minutes",
            min_value=5,
            max_value=120,
            value=default_reassess,
            step=5,
            key=f"followup_reassess_{assessment_id}",
        )
        followup_notes = st.text_area(
            "Follow-up notes",
            placeholder="Example: Moved to shaded area and started cooling.",
            height=90 if final_risk == "LOW" else 120,
            key=f"followup_notes_{assessment_id}",
        )
        save_label = "Save optional follow-up" if final_risk == "LOW" else "Save response actions"
        if st.button(save_label, key=f"save_followup_{assessment_id}"):
            if selected_actions:
                save_followup_actions(
                    assessment_id=assessment_id,
                    patient_name=patient_name,
                    action_labels=selected_actions,
                    notes=followup_notes,
                    reassess_minutes=int(reassess_minutes),
                )
                st.success("Follow-up actions saved.")
            else:
                st.warning("Select at least one action before saving.")

# ================= TAB 1: LIVE SCREENING =================
with tab_pred:
    st.markdown("### Live Heat Stress Screening")
    st.write("Complete the short workflow below to estimate heat-illness risk and get immediate action guidance.")
    if st.session_state.get("reassessment_context"):
        st.info(st.session_state["reassessment_context"])
    
    # Symptom description block
    with st.container(border=True):
        st.markdown("<h4>Step 1: Describe symptoms</h4>", unsafe_allow_html=True)
        nlp_text = st.text_area(
            "What is the person experiencing right now?",
            placeholder="Example: I feel extremely dizzy and nauseous with a throbbing headache.",
            height=120,
            key="nlp_description_input"
        )
        if st.button("Check symptoms", help="Suggests tracked symptoms from the description. You can confirm or change them before screening."):
            if nlp_text.strip() != "":
                with st.spinner("Checking symptom description..."):
                    nlp_res = extract_symptoms(nlp_text)
                    st.session_state.nlp_result = nlp_res
                    st.session_state.nlp_flags = nlp_res["flags"]
                    st.session_state.nlp_scores = nlp_res["scores"]
                    for symptom, detected in nlp_res["flags"].items():
                        st.session_state[f"nlp_accept_{symptom}"] = bool(detected)
                    st.success("Symptom suggestions are ready. Confirm them below before screening.")
            else:
                st.warning("Please describe the symptoms first.")

    nlp_result = st.session_state.get("nlp_result", None)
    accepted_nlp_flags = render_nlp_review_panel(nlp_result) if nlp_result else {}
    if accepted_nlp_flags and st.button("Apply selected symptoms"):
        st.session_state.symptom_dizziness = bool(accepted_nlp_flags.get("Dizziness", 0))
        st.session_state.symptom_headache = bool(accepted_nlp_flags.get("Headache", 0))
        st.session_state.symptom_cramps = bool(accepted_nlp_flags.get("MuscleCramps", 0))
        st.session_state.symptom_nausea = bool(accepted_nlp_flags.get("Nausea", 0))
        st.session_state.symptom_confusion = bool(accepted_nlp_flags.get("Confusion", 0))
        st.success("Selected symptoms applied to the screening form.")

    # Get values populated from reviewed NLP detections if available
    nlp_flags = accepted_nlp_flags or st.session_state.get("nlp_flags", {})
    diz_val = bool(nlp_flags.get("Dizziness", False))
    head_val = bool(nlp_flags.get("Headache", False))
    cramp_val = bool(nlp_flags.get("MuscleCramps", False))
    nausea_val = bool(nlp_flags.get("Nausea", False))
    conf_val = bool(nlp_flags.get("Confusion", False))
    
    # 2-column input layout: Left = Environmental, Right = Physiological
    col_env, col_phys = st.columns(2)
    
    with col_env:
        with st.container(border=True):
            st.markdown("<h4>Step 2: Environment</h4>", unsafe_allow_html=True)
            
            # Weather Lookup Widget
            city_input = st.text_input("City for live weather", "Delhi", help="Enter a city name to populate local temperature and humidity instantly.")
            if st.button("Fetch Live Weather"):
                with st.spinner("Retrieving weather conditions..."):
                    weather_data = get_live_weather(city_input)
                    if weather_data["success"]:
                        st.session_state.temp = weather_data["temp"]
                        st.session_state.humidity = weather_data["humidity"]
                        st.session_state.outdoor_temp_input = weather_data["temp"]
                        st.session_state.humidity_input = weather_data["humidity"]
                        st.success(f"Loaded {weather_data['city']}: {weather_data['temp']}°C, {weather_data['humidity']}% Humidity ({weather_data['description']})")
                    else:
                        st.warning("Could not reach weather API. Falling back to manual values.")
            
            # Environmental sliders (initialize using session state if fetched)
            default_temp = st.session_state.get("temp", 35.0)
            default_humidity = st.session_state.get("humidity", 50.0)
            
            outdoor_temp = st.slider("Ambient Temperature (°C)", 15.0, 50.0, float(default_temp), 0.1, help="Actual shade temperature outside.", key="outdoor_temp_input")
            humidity = st.slider("Relative Humidity (%)", 5.0, 100.0, float(default_humidity), 1.0, help="Humidity slows down sweat evaporation.", key="humidity_input")
            
            # Interactive Heat Index calculation
            heat_idx = calculate_heat_index(outdoor_temp, humidity)
            
            # Display apparent temperature status
            hi_color = "green" if heat_idx < 33 else "orange" if heat_idx < 41 else "red"
            st.markdown(f"**Apparent Temperature (Heat Index):** <span style='color:{hi_color}; font-weight:bold; font-size:1.15rem;'>{heat_idx:.1f} °C</span>", unsafe_allow_html=True)
            
            if heat_idx >= 41.0:
                st.error("🚨 **Extreme Danger Zone:** High risk of heat cramps, exhaustion, or heatstroke under prolonged exposure.")
            elif heat_idx >= 33.0:
                st.warning("⚠️ **Extreme Caution Zone:** Sunstroke, muscle cramps, and heat exhaustion possible with activity.")
            else:
                st.info("✅ **Caution/Normal Zone:** Lower atmospheric threat. Monitor body strain during high exertion.")
        
    with col_phys:
        with st.container(border=True):
            st.markdown("<h4>Step 3: Person and vitals</h4>", unsafe_allow_html=True)
            
            # Demographics
            pat_name = st.text_input("Patient Name / ID", "Anonymous", key="patient_name_input")
            col_dem1, col_dem2 = st.columns(2)
            with col_dem1:
                age = st.number_input("Age (Years)", 1, 120, 28, key="age_input")
                weight = st.number_input("Weight (kg)", 10.0, 200.0, 70.0, 0.5, key="weight_input")
            with col_dem2:
                height = st.number_input("Height (m)", 0.5, 2.5, 1.75, 0.01, key="height_input")
                heart_rate = st.slider("Heart Rate (bpm)", 50, 200, 80, help="Resting or active pulse.", key="heart_rate_input")
                
            bmi = round(weight / (height ** 2), 2) if height > 0 else 0.0
            st.write(f"**Body Mass Index (BMI):** `{bmi:.2f}`")

            patient_timeline = get_patient_timeline(pat_name, age=age, height_m=height)
            patient_profile = build_patient_profile(patient_timeline)
            if pat_name.strip() and pat_name.strip().casefold() != "anonymous":
                with st.expander("Patient memory", expanded=patient_profile["assessment_count"] > 0):
                    st.write(patient_profile["summary"])
                    st.caption("Matched using Patient Name / ID + Age + Height. Older records without saved height use name + age.")
                    if patient_profile["baseline_body_temp"] is not None:
                        mem_col1, mem_col2, mem_col3 = st.columns(3)
                        mem_col1.metric("Prior Screenings", patient_profile["assessment_count"])
                        mem_col2.metric("Baseline Body Temp", f"{patient_profile['baseline_body_temp']:.1f} C")
                        mem_col3.metric("Baseline Hydration", f"{patient_profile['baseline_hydration']:.1f} L")
            
            st.markdown("---")
            
            # Body Vitals
            body_temp = st.slider("Internal Body Temperature (°C)", 35.5, 43.0, 37.0, 0.1, help="Measured orally, tympanically, or rectally. Over 39°C points to hyperthermia.", key="body_temp_input")
            water_intake = st.slider("Today's Hydration Intake (Liters)", 0.0, 6.0, 2.0, 0.1, help="Recommended intake is > 2.5L in heat.", key="water_intake_input")
            
            # Symptoms Checkbox
            st.markdown("**Active Symptoms:**")
            col_sym1, col_sym2 = st.columns(2)
            with col_sym1:
                dizziness = st.checkbox("Severe Dizziness / Vertigo", value=diz_val, key="symptom_dizziness")
                headache = st.checkbox("Throbbing Headache", value=head_val, key="symptom_headache")
                muscle_cramps = st.checkbox("Muscle Cramps / Spasms", value=cramp_val, key="symptom_cramps")
            with col_sym2:
                nausea = st.checkbox("Nausea / Vomiting", value=nausea_val, key="symptom_nausea")
                confusion = st.checkbox("Confusion / Delirium", value=conf_val, key="symptom_confusion")

    # ACTION BUTTON
    st.markdown("---")
    if st.button("Run Heat Stress Screening", use_container_width=True):
        diz_int = 1 if dizziness else 0
        head_int = 1 if headache else 0
        cramp_int = 1 if muscle_cramps else 0
        nausea_int = 1 if nausea else 0
        conf_int = 1 if confusion else 0
        
        screening = run_screening(
            age=age,
            body_temp=body_temp,
            water_intake=water_intake,
            dizziness=diz_int,
            headache=head_int,
            heart_rate=heart_rate,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            muscle_cramps=cramp_int,
            nausea=nausea_int,
            confusion=conf_int
        )
        result = screening["ml_result"]
        risk = result["predicted_risk"]
        confidence = result["confidence"]
        heat_index_val = result["heat_index"]
        probabilities = result["probabilities"]
        safety_result = screening["safety_result"]
        final_risk = screening["final_risk"]
        model_metadata = screening["model_metadata"]
        
        # Save assessment to SQLite database with new columns
        assessment_id = save_record(
            patient_name=pat_name,
            age=age,
            body_temp=body_temp,
            water_intake=water_intake,
            dizziness=diz_int,
            headache=head_int,
            heart_rate=heart_rate,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            heat_index=heat_index_val,
            calculated_bmi=bmi,
            predicted_risk=final_risk,
            confidence=confidence,
            height_m=height,
            weight_kg=weight,
            muscle_cramps=cramp_int,
            nausea=nausea_int,
            confusion=conf_int,
            ml_risk=risk,
            final_risk=final_risk,
            safety_override_applied=safety_result["override_applied"],
            safety_override_reasons=safety_result["override_reasons"],
            model_type=model_metadata["model_type"],
            model_training_date=model_metadata["training_date"],
            model_accuracy=model_metadata["accuracy"],
            rule_engine_version=safety_result["rule_engine_version"],
        )
        log_audit_event(
            "assessment_recorded",
            entity_type="assessment",
            entity_id=assessment_id,
            details={
                "patient_name": pat_name,
                "ml_risk": risk,
                "final_risk": final_risk,
                "safety_override_applied": safety_result["override_applied"],
                "model_type": model_metadata["model_type"],
                "model_training_date": model_metadata["training_date"],
                "rule_engine_version": safety_result["rule_engine_version"],
            },
        )
        
        # Trigger client-side browser text-to-speech voice alert!
        alert_msg = f"Alert. Screening completed. Final heat stress risk is {final_risk}."
        if final_risk == "HIGH":
            alert_msg = "Critical Warning. High heatstroke risk detected. Initiate emergency cooling protocols."
        elif final_risk == "MEDIUM":
            alert_msg = "Attention. Moderate risk detected. Stop activity and hydrate immediately."
            
        speak_browser(alert_msg)
        
        risk_drivers = screening["risk_drivers"]
        model_explanation = screening["model_explanation"]
        
        # Display Results Panel
        st.markdown("### Screening Result")
        if safety_result["override_applied"]:
            st.warning(
                f"Safety override applied: ML estimated {risk}, final screening risk is {final_risk}. "
                + " ".join(safety_result["override_reasons"])
            )
        render_result_overview(final_risk, confidence, body_temp, water_intake, heart_rate, heat_index_val, bmi)
        render_emergency_checklist(final_risk)
        col_res1, col_res2 = st.columns([1, 1.2])
        
        with col_res1:
            with st.container(border=True):
                st.markdown("<h4>Risk Probability</h4>", unsafe_allow_html=True)
                
                # Map colors for the gauge chart based on prediction risk
                gauge_color = "#2ecc71" if final_risk == "LOW" else "#f1c40f" if final_risk == "MEDIUM" else "#e74c3c"
                
                # Plotly Gauge Chart
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=confidence,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 100], 'ticksuffix': "%"},
                        'bar': {'color': gauge_color},
                        'bgcolor': "rgba(0,0,0,0.03)",
                        'steps': [
                            {'range': [0, 35], 'color': 'rgba(46, 204, 113, 0.15)'},
                            {'range': [35, 70], 'color': 'rgba(241, 196, 15, 0.15)'},
                            {'range': [70, 100], 'color': 'rgba(231, 76, 60, 0.15)'}
                        ],
                    }
                ))
                fig.update_layout(
                    height=250, 
                    margin=dict(l=15, r=15, t=30, b=15),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed probabilities table
                st.write("**Risk Class Breakdown:**")
                st.progress(probabilities["LOW"] / 100.0, text=f"🟢 Low Risk Probability: {probabilities['LOW']}%")
                st.progress(probabilities["MEDIUM"] / 100.0, text=f"🟡 Medium Risk Probability: {probabilities['MEDIUM']}%")
                st.progress(probabilities["HIGH"] / 100.0, text=f"🔴 High Risk Probability: {probabilities['HIGH']}%")
                st.caption(f"Model estimate: {risk}. Final risk can be raised by safety rules when red-flag symptoms are present.")
            render_followup_panel(final_risk, assessment_id, pat_name)
            
        with col_res2:
            render_risk_driver_panel(risk_drivers)
            render_model_explanation_panel(model_explanation)
            
            # Custom action guidance card
            recs = get_health_recommendations(final_risk, body_temp, water_intake, bmi)
            
            # Render risk banner in a single HTML block
            banner_style = "emergency-box" if final_risk == "HIGH" else "glass-card"
            badge_class = f"badge badge-{recs['indicator']}"
            
            actions_li = "".join([f"<li>{act.replace('**', '<strong>', 1).replace('**', '</strong>', 1)}</li>" for act in recs['actions']])
            
            html_card = f"""
            <div class='{banner_style}'>
                <h3 style='margin-top:0; color:inherit;'>{recs['title']} <span class='{badge_class}'>{final_risk} RISK</span></h3>
                <p style='color:inherit;'>{recs['summary']}</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.15); margin: 1rem 0;'>
                <strong style='color:inherit;'>Recommended Action Steps:</strong>
                <ul style='margin-top: 0.5rem; padding-left: 1.2rem; color:inherit;'>
                    {actions_li}
                </ul>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)

# ================= TAB 2: MONITORING DASHBOARD =================
with tab_analytics:
    st.markdown("### Heat Risk Monitoring Dashboard")
    st.write("Monitor current heat-risk screenings, review urgent cases, and explore population-level risk patterns.")
    
    records = get_all_records()
    
    if not records:
        st.warning("No assessment logs are available yet. Use Live Screening or load demo data from the sidebar admin tools.")
    else:
        df_logs = pd.DataFrame(records)
        df_logs["timestamp"] = pd.to_datetime(df_logs["timestamp"])
        df_logs = df_logs.sort_values("timestamp")
        df_logs["Run"] = range(1, len(df_logs) + 1)
        df_logs["source"] = df_logs["simulation_batch_id"].apply(lambda val: "Simulation" if pd.notna(val) and val else "Manual")
        followup_records = get_recent_followups(limit=500)
        if followup_records:
            df_followups = pd.DataFrame(followup_records)
            df_followups["timestamp"] = pd.to_datetime(df_followups["timestamp"])
            latest_followups = (
                df_followups.sort_values("timestamp")
                .drop_duplicates("assessment_id", keep="last")
                .set_index("assessment_id")
            )
            followup_time_map = latest_followups["timestamp"].to_dict()
            followup_reassess_map = latest_followups["reassess_minutes"].to_dict()
            followup_action_map = latest_followups["action_labels"].to_dict()
        else:
            followup_time_map = {}
            followup_reassess_map = {}
            followup_action_map = {}

        df_logs["followup_recorded"] = df_logs["id"].apply(lambda record_id: record_id in followup_time_map)
        df_logs["followup_time"] = df_logs["id"].map(followup_time_map)
        df_logs["followup_reassess_minutes"] = df_logs["id"].map(followup_reassess_map)
        df_logs["reassess_due_at"] = df_logs.apply(
            lambda row: (
                row["followup_time"] + pd.Timedelta(minutes=int(row["followup_reassess_minutes"]))
                if pd.notna(row["followup_time"]) and pd.notna(row["followup_reassess_minutes"])
                else pd.NaT
            ),
            axis=1,
        )
        current_time = pd.Timestamp(datetime.now())
        df_logs["reassessment_due"] = df_logs["reassess_due_at"].apply(
            lambda due_at: pd.notna(due_at) and due_at <= current_time
        )

        total_records = len(df_logs)
        all_high_count = len(df_logs[df_logs["predicted_risk"] == "HIGH"])
        all_medium_count = len(df_logs[df_logs["predicted_risk"] == "MEDIUM"])
        all_avg_body_temp = round(df_logs["body_temp"].mean(), 2) if total_records else 0.0
        all_avg_water = round(df_logs["water_intake"].mean(), 2) if total_records else 0.0
        manual_count = len(df_logs[df_logs["source"] == "Manual"])
        simulation_count = len(df_logs[df_logs["source"] == "Simulation"])

        summary_col1, summary_col2, summary_col3, summary_col4, summary_col5, summary_col6 = st.columns(6)
        summary_col1.metric("Screenings", f"{total_records}")
        summary_col2.metric("High Risk", f"{all_high_count}")
        summary_col3.metric("Medium Risk", f"{all_medium_count}")
        summary_col4.metric("Avg Body Temp", f"{all_avg_body_temp} C")
        summary_col5.metric("Avg Hydration", f"{all_avg_water} L")
        summary_col6.metric("Manual / Sim", f"{manual_count} / {simulation_count}")

        timeline_map = {
            patient: group.sort_values("timestamp").to_dict("records")
            for patient, group in df_logs.groupby("patient_name")
        }
        triage_results = [
            calculate_triage_priority(row.to_dict(), timeline_map.get(row.get("patient_name"), []))
            for _, row in df_logs.iterrows()
        ]
        df_logs["triage_score"] = [result["score"] for result in triage_results]
        df_logs["triage_priority"] = [result["priority"] for result in triage_results]
        df_logs["needs_reassessment"] = [result["needs_reassessment"] for result in triage_results]
        df_logs["triage_reasons"] = [", ".join(result["reasons"][:3]) for result in triage_results]
        df_logs["followup_status"] = df_logs.apply(
            lambda row: (
                "Reassessment due" if row["reassessment_due"]
                else "Recorded" if row["followup_recorded"]
                else "Missing" if row["needs_reassessment"]
                else "Optional"
            ),
            axis=1,
        )

        needs_reassessment_count = int(df_logs["needs_reassessment"].sum())
        missing_followup_count = int(((df_logs["needs_reassessment"]) & (~df_logs["followup_recorded"])).sum())
        reassessment_due_count = int(df_logs["reassessment_due"].sum())
        if needs_reassessment_count:
            st.warning(f"{needs_reassessment_count} assessment(s) need reassessment or follow-up review.")
        if missing_followup_count:
            st.error(f"{missing_followup_count} priority assessment(s) are missing recorded follow-up actions.")
        if reassessment_due_count:
            st.warning(f"{reassessment_due_count} saved follow-up plan(s) are due for reassessment.")

        st.markdown("#### Priority Triage Queue")
        priority_queue = df_logs[
            (df_logs["predicted_risk"] == "HIGH") | (df_logs["needs_reassessment"])
        ].sort_values(
            ["triage_score", "timestamp", "body_temp", "heat_index"],
            ascending=[False, False, False, False]
        ).head(8)
        if priority_queue.empty:
            st.success("No urgent reassessment alerts are currently in the monitoring queue.")
        else:
            with st.container(border=True):
                st.error(f"{len(priority_queue)} person(s) need review in the triage queue.")
                queue_view = priority_queue.copy()
                queue_view["Red Flag"] = queue_view["confusion"].apply(lambda val: "Confusion" if int(val) == 1 else "None selected")
                queue_view["Action Needed"] = queue_view.apply(
                    lambda row: "Emergency review" if int(row.get("confusion", 0)) == 1 or float(row.get("body_temp", 0)) >= 40.0 else "Cool, hydrate, reassess",
                    axis=1
                )
                queue_view["Needs Reassessment"] = queue_view["needs_reassessment"].apply(lambda val: "Yes" if bool(val) else "No")
                queue_view["Reassessment Due"] = queue_view["reassessment_due"].apply(lambda val: "Yes" if bool(val) else "No")
                queue_view["Due At"] = queue_view["reassess_due_at"].apply(
                    lambda val: val.strftime("%Y-%m-%d %H:%M") if pd.notna(val) else "-"
                )
                queue_view = queue_view.rename(columns={
                    "timestamp": "Time",
                    "patient_name": "Person / ID",
                    "source": "Source",
                    "predicted_risk": "Risk",
                    "body_temp": "Body Temp (C)",
                    "heart_rate": "Heart Rate",
                    "heat_index": "Heat Index (C)",
                    "water_intake": "Hydration (L)",
                    "triage_priority": "Priority",
                    "triage_score": "Score",
                    "triage_reasons": "Reason",
                    "followup_status": "Follow-up",
                })
                queue_cols = [
                    "Time", "Person / ID", "Priority", "Score", "Risk", "Body Temp (C)",
                    "Heat Index (C)", "Heart Rate", "Hydration (L)", "Needs Reassessment",
                    "Follow-up", "Reassessment Due", "Due At", "Reason", "Action Needed"
                ]
                st.dataframe(
                    queue_view[queue_cols],
                    use_container_width=True,
                    hide_index=True
                )
                reassess_options = priority_queue.index.tolist()
                selected_reassess_index = st.selectbox(
                    "Choose person to reassess",
                    reassess_options,
                    key="reassess_patient_select",
                    format_func=lambda idx: (
                        f"{priority_queue.loc[idx, 'patient_name']} - "
                        f"{priority_queue.loc[idx, 'predicted_risk']} risk - "
                        f"score {priority_queue.loc[idx, 'triage_score']}"
                    ),
                )
                if st.button("Prepare reassessment in Live Screening", key="prepare_reassessment"):
                    selected_record = priority_queue.loc[selected_reassess_index].to_dict()
                    st.session_state.pending_reassessment_prefill = build_reassessment_prefill(selected_record)
                    st.session_state.pending_reassessment_context = (
                        f"Reassessment prepared for {selected_record.get('patient_name')} "
                        f"from {selected_record.get('timestamp')}."
                    )
                    st.rerun()
        
        with st.expander("Filter records", expanded=False):
            filt_col1, filt_col2, filt_col3 = st.columns(3)
            with filt_col1:
                selected_risks = st.multiselect(
                    "Risk levels",
                    ["LOW", "MEDIUM", "HIGH"],
                    default=["LOW", "MEDIUM", "HIGH"],
                    key="analytics_risk_filter"
                )
                selected_sources = st.multiselect(
                    "Assessment source",
                    ["Manual", "Simulation"],
                    default=["Manual", "Simulation"],
                    key="analytics_source_filter"
                )
            with filt_col2:
                patient_options = sorted([p for p in df_logs["patient_name"].dropna().unique()])
                selected_patients = st.multiselect(
                    "Person / ID",
                    patient_options,
                    default=[],
                    help="Leave empty to include all patients.",
                    key="analytics_patient_filter"
                )
                min_date = df_logs["timestamp"].dt.date.min()
                max_date = df_logs["timestamp"].dt.date.max()
                date_range = st.date_input(
                    "Date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="analytics_date_filter"
                )
            with filt_col3:
                body_temp_min = float(df_logs["body_temp"].min())
                body_temp_max = float(df_logs["body_temp"].max())
                if body_temp_min == body_temp_max:
                    body_temp_max = body_temp_min + 0.1
                heat_index_min = float(df_logs["heat_index"].min())
                heat_index_max = float(df_logs["heat_index"].max())
                if heat_index_min == heat_index_max:
                    heat_index_max = heat_index_min + 0.1
                temp_range = st.slider(
                    "Body temperature range",
                    body_temp_min,
                    body_temp_max,
                    (body_temp_min, body_temp_max),
                    0.1,
                    key="analytics_temp_filter"
                )
                heat_range = st.slider(
                    "Heat index range",
                    heat_index_min,
                    heat_index_max,
                    (heat_index_min, heat_index_max),
                    0.1,
                    key="analytics_heat_filter"
                )

        df_filtered = df_logs.copy()
        df_filtered = df_filtered[df_filtered["predicted_risk"].isin(selected_risks)]
        df_filtered = df_filtered[df_filtered["source"].isin(selected_sources)]
        if selected_patients:
            df_filtered = df_filtered[df_filtered["patient_name"].isin(selected_patients)]
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df_filtered[
                (df_filtered["timestamp"].dt.date >= start_date) &
                (df_filtered["timestamp"].dt.date <= end_date)
            ]
        df_filtered = df_filtered[
            df_filtered["body_temp"].between(temp_range[0], temp_range[1]) &
            df_filtered["heat_index"].between(heat_range[0], heat_range[1])
        ].copy()
        df_filtered = df_filtered.sort_values("timestamp")
        df_filtered["Run"] = range(1, len(df_filtered) + 1)

        if df_filtered.empty:
            st.warning("No records match the selected filters. Relax one or more filters to view analytics.")

        csv_filtered = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download report",
            data=csv_filtered,
            file_name=f"filtered_heatstroke_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # 1. Individual Time-Series tracking (Phase 3)
        st.markdown("#### Person Risk Timeline")
        patient_counts = df_filtered[df_filtered["patient_name"] != "Anonymous"]["patient_name"].value_counts()
        patient_names = patient_counts.index.tolist()
        if patient_names:
            col_t1, col_t2 = st.columns([1, 1.7])
            with col_t1:
                selected_patient = st.selectbox(
                    "Select person to view history:",
                    patient_names,
                    format_func=lambda name: f"{name} ({patient_counts.get(name, 0)} screenings)"
                )
                timeline = df_filtered[df_filtered["patient_name"] == selected_patient].sort_values("timestamp").to_dict("records")
                patient_latest = timeline[-1] if timeline else {}

                if len(timeline) >= 2:
                    trend = detect_risk_trend(timeline)
                    if trend["status"] == "CRITICAL ESCALATION":
                        st.error(trend["message"])
                    elif "RISK ESCALATING" in trend["status"] or "TEMP RISING" in trend["status"]:
                        st.warning(trend["message"])
                    else:
                        st.success(trend["message"])
                else:
                    st.info("Trend will appear after one more screening for this person.")

                if patient_latest:
                    st.metric("Latest Risk", patient_latest.get("predicted_risk", "N/A"))
                    st.metric("Latest Body Temp", f"{patient_latest.get('body_temp', 0):.1f} C")
                    st.metric("Assessments in Filter", len(timeline))
                    latest_id = patient_latest.get("id")
                    latest_followup_status = patient_latest.get("followup_status", "Optional")
                    if latest_followup_status == "Reassessment due":
                        st.warning("Follow-up status: reassessment is due now.")
                    elif latest_followup_status == "Recorded":
                        st.success("Follow-up status: completed actions recorded.")
                    elif latest_followup_status == "Missing":
                        st.error("Follow-up status: action record needed.")
                    else:
                        st.info("Follow-up status: optional monitoring.")
                    if latest_id in followup_action_map:
                        try:
                            latest_actions = json.loads(followup_action_map.get(latest_id) or "[]")
                        except json.JSONDecodeError:
                            latest_actions = []
                        if latest_actions:
                            st.caption("Latest actions: " + ", ".join(latest_actions[:2]))

            with col_t2:
                if len(timeline) >= 2:
                    df_time = pd.DataFrame(timeline)
                    df_time['timestamp'] = pd.to_datetime(df_time['timestamp'])
                    df_time = df_time.sort_values("timestamp")
                    
                    fig_time = px.line(
                        df_time, 
                        x="timestamp", 
                        y="body_temp", 
                        title=f"Risk trend for {selected_patient}",
                        markers=True,
                        color_discrete_sequence=["#e74c3c"]
                    )
                    fig_time.add_scatter(
                        x=df_time["timestamp"], 
                        y=df_time["heat_index"], 
                        mode="lines+markers", 
                        name="Heat Index (°C)",
                        line=dict(color="#f39c12", dash='dash')
                    )
                    fig_time.update_layout(height=280, margin=dict(t=40, b=20, l=10, r=10))
                    st.plotly_chart(fig_time, use_container_width=True)
                elif patient_latest:
                    with st.container(border=True):
                        st.markdown("<h5>Latest assessment snapshot</h5>", unsafe_allow_html=True)
                        snap_col1, snap_col2, snap_col3, snap_col4 = st.columns(4)
                        snap_col1.metric("Risk", patient_latest.get("predicted_risk", "N/A"))
                        snap_col2.metric("Heat Index", f"{patient_latest.get('heat_index', 0):.1f} C")
                        snap_col3.metric("Heart Rate", f"{patient_latest.get('heart_rate', 0)} bpm")
                        snap_col4.metric("Hydration", f"{patient_latest.get('water_intake', 0):.1f} L")
                        st.caption("Record one more screening for this person to unlock the trend chart.")
        else:
            st.info("Enter non-Anonymous person IDs in Live Screening to track individual trends.")
            
        st.markdown("---")
        
        # 2. KPIs Row
        st.markdown("#### Filtered Summary")
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        total_runs = len(df_filtered)
        high_risk_runs = len(df_filtered[df_filtered["predicted_risk"] == "HIGH"])
        high_risk_percentage = round((high_risk_runs / total_runs) * 100, 1) if total_runs else 0.0
        avg_body_temp = round(df_filtered["body_temp"].mean(), 2) if total_runs else 0.0
        avg_water = round(df_filtered["water_intake"].mean(), 2) if total_runs else 0.0
        
        kpi_col1.metric("Filtered Screenings", f"{total_runs}", "records")
        kpi_col2.metric("High-Risk Cases", f"{high_risk_runs}", f"{high_risk_percentage}% of filtered", delta_color="inverse" if high_risk_percentage > 15 else "normal")
        kpi_col3.metric("Average Body Temp", f"{avg_body_temp} C", "Normal is 37 C")
        kpi_col4.metric("Average Hydration", f"{avg_water} L", "Target: > 2.5 L")
        
        st.markdown("---")
        
        # 3. Charts Row 1: Risk Distribution vs Vitals Trends
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            with st.container(border=True):
                st.markdown("<h5>Current Risk Distribution</h5>", unsafe_allow_html=True)
                risk_counts = df_filtered["predicted_risk"].value_counts().reset_index()
                risk_counts.columns = ["Risk Level", "Count"]
                colors_map = {'LOW': '#2ecc71', 'MEDIUM': '#f1c40f', 'HIGH': '#e74c3c'}
                
                fig_pie = px.pie(
                    risk_counts, 
                    values='Count', 
                    names='Risk Level', 
                    hole=0.4,
                    color='Risk Level',
                    color_discrete_map=colors_map
                )
                fig_pie.update_layout(height=280, margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
            
        with chart_col2:
            with st.container(border=True):
                st.markdown("<h5>Body Temperature & Heart Rate Trend</h5>", unsafe_allow_html=True)
                fig_trend = px.line(
                    df_filtered, 
                    x="Run", 
                    y=["body_temp", "heart_rate"], 
                    labels={"value": "Vital Measure", "variable": "Indicator"},
                    markers=True,
                    color_discrete_sequence=["#e74c3c", "#3498db"]
                )
                fig_trend.update_layout(height=280, margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_trend, use_container_width=True)
            
        # 4. Charts Row 2: Risk factor importance and model performance details
        chart_col3, chart_col4 = st.columns(2)
        
        with chart_col3:
            with st.container(border=True):
                st.markdown("<h5>Top Factors Affecting Risk</h5>", unsafe_allow_html=True)
                importances = get_feature_importances()
                if importances:
                    imp_df = pd.DataFrame(list(importances.items()), columns=["Feature", "Importance"]).sort_values("Importance", ascending=True)
                    fig_imp = px.bar(
                        imp_df, 
                        x="Importance", 
                        y="Feature", 
                        orientation='h',
                        color="Importance",
                        color_continuous_scale="OrRd"
                    )
                    fig_imp.update_layout(height=280, margin=dict(t=20, b=20, l=10, r=10), showlegend=False)
                    st.plotly_chart(fig_imp, use_container_width=True)
                else:
                    st.info("Feature importance data not found. Train the model to see insights.")
            
        with chart_col4:
            with st.expander("Model performance details", expanded=False):
                st.caption("Technical validation view for the trained risk model.")
                conf_matrix = get_confusion_matrix()
                if conf_matrix:
                    fig_conf = px.imshow(
                        conf_matrix,
                        labels=dict(x="Predicted Class", y="Actual Class", color="Count"),
                        x=["Low", "Medium", "High"],
                        y=["Low", "Medium", "High"],
                        text_auto=True,
                        color_continuous_scale="Reds"
                    )
                    fig_conf.update_layout(height=280, margin=dict(t=20, b=20, l=10, r=10))
                    st.plotly_chart(fig_conf, use_container_width=True)
                else:
                    st.info("Model validation matrix unavailable.")

        st.markdown("---")
        st.markdown("#### 🧭 Risk Pattern Explorer")
        pattern_col1, pattern_col2 = st.columns(2)
        symptom_cols = ["dizziness", "headache", "muscle_cramps", "nausea", "confusion"]
        symptom_labels = {
            "dizziness": "Dizziness",
            "headache": "Headache",
            "muscle_cramps": "Muscle Cramps",
            "nausea": "Nausea",
            "confusion": "Confusion"
        }

        with pattern_col1:
            with st.container(border=True):
                st.markdown("<h5>Symptoms by Risk Level</h5>", unsafe_allow_html=True)
                if not df_filtered.empty:
                    symptom_matrix = (
                        df_filtered.groupby("predicted_risk")[symptom_cols]
                        .mean()
                        .reindex(["LOW", "MEDIUM", "HIGH"])
                        .fillna(0)
                        * 100
                    )
                    symptom_matrix = symptom_matrix.rename(columns=symptom_labels)
                    fig_symptom_heat = px.imshow(
                        symptom_matrix,
                        labels=dict(x="Symptom", y="Risk Level", color="% Present"),
                        text_auto=".1f",
                        color_continuous_scale="YlOrRd",
                        aspect="auto"
                    )
                    fig_symptom_heat.update_layout(height=300, margin=dict(t=20, b=20, l=10, r=10))
                    st.plotly_chart(fig_symptom_heat, use_container_width=True)
                else:
                    st.info("No filtered records available for symptom analysis.")

        with pattern_col2:
            with st.container(border=True):
                st.markdown("<h5>Heat Exposure vs Body Temperature</h5>", unsafe_allow_html=True)
                if not df_filtered.empty:
                    fig_scatter = px.scatter(
                        df_filtered,
                        x="heat_index",
                        y="body_temp",
                        color="predicted_risk",
                        size="confidence",
                        hover_data=["patient_name", "heart_rate", "water_intake", "source"],
                        color_discrete_map=colors_map,
                        labels={
                            "heat_index": "Heat Index (C)",
                            "body_temp": "Body Temperature (C)",
                            "predicted_risk": "Risk"
                        }
                    )
                    fig_scatter.add_hline(y=39.5, line_dash="dash", line_color="#e74c3c", annotation_text="High temp concern")
                    fig_scatter.add_vline(x=41.0, line_dash="dash", line_color="#f39c12", annotation_text="Extreme heat index")
                    fig_scatter.update_layout(height=300, margin=dict(t=20, b=20, l=10, r=10))
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.info("No filtered records available for exposure plotting.")

        insight_col1, insight_col2 = st.columns(2)
        with insight_col1:
            with st.container(border=True):
                st.markdown("<h5>Most Common High-Risk Factors</h5>", unsafe_allow_html=True)
                high_df = df_filtered[df_filtered["predicted_risk"] == "HIGH"]
                if not high_df.empty:
                    factor_rates = {
                        "Body temp >= 39.5 C": (high_df["body_temp"] >= 39.5).mean() * 100,
                        "Heat index >= 41 C": (high_df["heat_index"] >= 41.0).mean() * 100,
                        "Water intake < 2 L": (high_df["water_intake"] < 2.0).mean() * 100,
                        "Heart rate >= 120": (high_df["heart_rate"] >= 120).mean() * 100,
                        "Confusion present": (high_df["confusion"] == 1).mean() * 100,
                        "Nausea present": (high_df["nausea"] == 1).mean() * 100,
                    }
                    factor_df = pd.DataFrame(
                        [{"Factor": key, "% of High-Risk Cases": round(value, 1)} for key, value in factor_rates.items()]
                    ).sort_values("% of High-Risk Cases", ascending=True)
                    fig_factors = px.bar(
                        factor_df,
                        x="% of High-Risk Cases",
                        y="Factor",
                        orientation="h",
                        color="% of High-Risk Cases",
                        color_continuous_scale="Reds",
                        range_x=[0, 100]
                    )
                    fig_factors.update_layout(height=300, margin=dict(t=20, b=20, l=10, r=10), showlegend=False)
                    st.plotly_chart(fig_factors, use_container_width=True)
                else:
                    st.info("No high-risk cases in the current filter.")

        with insight_col2:
            with st.container(border=True):
                st.markdown("<h5>Manual vs Simulation Mix</h5>", unsafe_allow_html=True)
                if not df_filtered.empty:
                    source_counts = df_filtered.groupby(["source", "predicted_risk"]).size().reset_index(name="Count")
                    fig_source = px.bar(
                        source_counts,
                        x="source",
                        y="Count",
                        color="predicted_risk",
                        barmode="group",
                        color_discrete_map=colors_map,
                        labels={"source": "Assessment Source", "predicted_risk": "Risk"}
                    )
                    fig_source.update_layout(height=300, margin=dict(t=20, b=20, l=10, r=10))
                    st.plotly_chart(fig_source, use_container_width=True)
                else:
                    st.info("No filtered records available for source comparison.")
                    
        # 5. Advanced records
        with st.expander("Advanced records", expanded=False):
            display_cols = [
                col for col in [
                    "timestamp", "patient_name", "source", "age", "calculated_bmi",
                    "body_temp", "water_intake", "heat_index", "ml_risk", "predicted_risk",
                    "safety_override_applied", "model_type", "model_training_date",
                    "rule_engine_version", "confidence"
                ] if col in df_filtered.columns
            ]
            records_view = df_filtered.sort_values("timestamp", ascending=False)[display_cols].rename(columns={
                "timestamp": "Time",
                "patient_name": "Person / ID",
                "source": "Source",
                "age": "Age",
                "calculated_bmi": "BMI",
                "body_temp": "Body Temp (C)",
                "water_intake": "Hydration (L)",
                "heat_index": "Heat Index (C)",
                "ml_risk": "Model Risk",
                "predicted_risk": "Final Risk",
                "safety_override_applied": "Safety Override",
                "model_type": "Model Type",
                "model_training_date": "Model Training Date",
                "rule_engine_version": "Rule Engine Version",
                "confidence": "Confidence"
            })
            st.dataframe(
                records_view,
                use_container_width=True,
                hide_index=True
            )

        with st.expander("Audit trail", expanded=False):
            audit_events = get_audit_events(limit=50)
            if audit_events:
                def parse_audit_details(raw_details):
                    if isinstance(raw_details, dict):
                        return raw_details
                    try:
                        return json.loads(raw_details or "{}")
                    except (TypeError, json.JSONDecodeError):
                        return {}

                def summarize_audit_event(row):
                    details = parse_audit_details(row.get("details"))
                    event = row.get("event_type", "")
                    if event == "assessment_recorded":
                        patient = details.get("patient_name", "Unknown person")
                        ml_risk = details.get("ml_risk", "N/A")
                        final_risk = details.get("final_risk", "N/A")
                        override = "override applied" if details.get("safety_override_applied") else "no override"
                        return f"{patient}: model {ml_risk}, final {final_risk}, {override}"
                    if event == "simulation_batch_completed":
                        scenario = details.get("scenario", "Simulation")
                        total = details.get("total_simulated", "N/A")
                        risk_counts = details.get("risk_counts", {})
                        high_count = risk_counts.get("HIGH", 0) if isinstance(risk_counts, dict) else 0
                        return f"{scenario}: {total} simulated, {high_count} high risk"
                    return str(row.get("details", ""))[:140]

                raw_audit_df = pd.DataFrame(audit_events)
                audit_df = pd.DataFrame(audit_events).rename(columns={
                    "timestamp": "Time",
                    "event_type": "Event",
                    "actor": "Actor",
                    "entity_type": "Entity Type",
                    "entity_id": "Entity ID",
                    "details": "Details"
                })
                audit_df["Summary"] = raw_audit_df.apply(summarize_audit_event, axis=1)
                audit_df["Event"] = audit_df["Event"].replace({
                    "assessment_recorded": "Assessment recorded",
                    "simulation_batch_completed": "Simulation completed"
                })
                st.dataframe(
                    audit_df[["Time", "Event", "Actor", "Entity Type", "Entity ID", "Summary"]],
                    use_container_width=True,
                    hide_index=True
                )
                with st.expander("Show raw audit details", expanded=False):
                    st.dataframe(
                        audit_df[["Time", "Event", "Details"]],
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info("No audit events recorded yet.")

# ================= TAB 3: SIMULATION LAB (Phase 4) =================
with tab_sim:
    st.markdown("### Scenario Impact Simulator")
    st.write("Test how climate, hydration, vitals, and symptoms could shift risk across a simulated group.")
    
    col_sim_c1, col_sim_c2 = st.columns([1, 1.2])
    
    with col_sim_c1:
        with st.container(border=True):
            st.markdown("<h4>Build scenario</h4>", unsafe_allow_html=True)
            scenario_mode = st.radio(
                "Scenario mode",
                ["Preset", "Custom"],
                horizontal=True,
                key="sim_scenario_mode"
            )
            preset_choice = st.selectbox(
                "Base climate profile", 
                ["Heatwave Delhi", "Monsoon Mumbai", "Normal Bangalore"],
                key="sim_scenario_select"
            )
            scenario_profile = get_scenario_profile(preset_choice)
            scenario_name = preset_choice
            scenario_notes = {
                "Heatwave Delhi": "Extreme dry heat with lower hydration and more frequent heat-illness symptoms.",
                "Monsoon Mumbai": "Humid heat stress where sweat evaporation is reduced and exertion risk can rise.",
                "Normal Bangalore": "Baseline lower-heat condition for comparing against higher-risk profiles.",
            }
            st.info(scenario_notes.get(preset_choice, "Custom scenario profile."))

            if scenario_mode == "Custom":
                scenario_name = f"Custom {preset_choice}"
                st.caption(f"Customizing profile: {scenario_name}")
                with st.expander("Customize scenario inputs", expanded=True):
                    st.markdown("**Environment and vital ranges**")
                    scenario_profile["outdoor_temp"] = st.slider(
                        "Ambient temperature range (C)",
                        15.0,
                        50.0,
                        scenario_profile["outdoor_temp"],
                        0.5,
                        key="sim_temp_range"
                    )
                    scenario_profile["humidity"] = st.slider(
                        "Humidity range (%)",
                        5.0,
                        100.0,
                        scenario_profile["humidity"],
                        1.0,
                        key="sim_humidity_range"
                    )
                    scenario_profile["water_intake"] = st.slider(
                        "Hydration intake range (L)",
                        0.0,
                        6.0,
                        scenario_profile["water_intake"],
                        0.1,
                        key="sim_water_range"
                    )
                    scenario_profile["body_temp"] = st.slider(
                        "Body temperature range (C)",
                        35.5,
                        43.0,
                        scenario_profile["body_temp"],
                        0.1,
                        key="sim_body_temp_range"
                    )
                    scenario_profile["heart_rate"] = st.slider(
                        "Heart rate range (bpm)",
                        50,
                        200,
                        scenario_profile["heart_rate"],
                        1,
                        key="sim_hr_range"
                    )

                    st.markdown("**Symptom chance (%)**")
                    prob_col1, prob_col2 = st.columns(2)
                    with prob_col1:
                        scenario_profile["symptoms"]["dizziness"] = st.slider("Dizziness", 0, 100, int(scenario_profile["symptoms"]["dizziness"] * 100), key="sim_prob_diz") / 100
                        scenario_profile["symptoms"]["headache"] = st.slider("Headache", 0, 100, int(scenario_profile["symptoms"]["headache"] * 100), key="sim_prob_head") / 100
                        scenario_profile["symptoms"]["muscle_cramps"] = st.slider("Muscle cramps", 0, 100, int(scenario_profile["symptoms"]["muscle_cramps"] * 100), key="sim_prob_cramp") / 100
                    with prob_col2:
                        scenario_profile["symptoms"]["nausea"] = st.slider("Nausea", 0, 100, int(scenario_profile["symptoms"]["nausea"] * 100), key="sim_prob_nausea") / 100
                        scenario_profile["symptoms"]["confusion"] = st.slider("Confusion", 0, 100, int(scenario_profile["symptoms"]["confusion"] * 100), key="sim_prob_conf") / 100
            else:
                st.caption("Preset ranges can be customized by switching to Custom mode.")

            with st.expander("Scenario preview", expanded=True):
                preview_col1, preview_col2 = st.columns(2)
                with preview_col1:
                    st.write(f"**Temperature:** {scenario_profile['outdoor_temp'][0]:.1f}-{scenario_profile['outdoor_temp'][1]:.1f} C")
                    st.write(f"**Humidity:** {scenario_profile['humidity'][0]:.0f}-{scenario_profile['humidity'][1]:.0f}%")
                    st.write(f"**Hydration:** {scenario_profile['water_intake'][0]:.1f}-{scenario_profile['water_intake'][1]:.1f} L")
                with preview_col2:
                    st.write(f"**Body temperature:** {scenario_profile['body_temp'][0]:.1f}-{scenario_profile['body_temp'][1]:.1f} C")
                    st.write(f"**Heart rate:** {scenario_profile['heart_rate'][0]}-{scenario_profile['heart_rate'][1]} bpm")
                    symptom_preview = ", ".join([
                        f"{name.replace('_', ' ')} {prob * 100:.0f}%"
                        for name, prob in scenario_profile["symptoms"].items()
                    ])
                    st.write(f"**Symptoms:** {symptom_preview}")

            fixed_seed_enabled = st.checkbox(
                "Use repeatable demo results",
                value=True,
                help="Keeps the same scenario reproducible during demos."
            )
            random_seed = None
            if fixed_seed_enabled:
                random_seed = st.number_input(
                    "Demo seed",
                    min_value=0,
                    max_value=999999,
                    value=2026,
                    step=1,
                    help="Run the same scenario with the same seed to reproduce the same simulated group."
                )

            cohort_size = st.slider("People to simulate:", 10, 500, 100, key="sim_cohort_slider")
            
            if st.button("Run Scenario", use_container_width=True):
                with st.spinner(f"Simulating {cohort_size} people under {scenario_name}..."):
                    sim_summary = run_cohort_simulation(
                        cohort_size,
                        scenario_name,
                        scenario_profile,
                        random_seed=int(random_seed) if random_seed is not None else None,
                    )
                    st.session_state.sim_summary = sim_summary
                    st.session_state.sim_scenario = scenario_name
                    st.success("Scenario completed. Results are ready.")
                    
    with col_sim_c2:
        sim_summary = st.session_state.get("sim_summary", None)
        selected_scenario = st.session_state.get("sim_scenario", "")
        if sim_summary:
            with st.container(border=True):
                st.markdown(f"<h4>Scenario results: {selected_scenario}</h4>", unsafe_allow_html=True)
                
                # KPIs
                col_sk1, col_sk2, col_sk3 = st.columns(3)
                col_sk1.metric("Average Heat Index", f"{sim_summary['avg_heat_index']} C")
                col_sk2.metric("Average Body Temp", f"{sim_summary['avg_body_temp']} C")
                col_sk3.metric("High Risk Cases", f"{sim_summary['risk_counts'].get('HIGH', 0)} / {sim_summary['total_simulated']}")
                
                # Plotly risk distribution pie chart for this batch
                df_batch_records = pd.DataFrame(get_records_by_batch(sim_summary["batch_id"]))
                
                if not df_batch_records.empty:
                    high_count = int(sim_summary["risk_counts"].get("HIGH", 0))
                    medium_count = int(sim_summary["risk_counts"].get("MEDIUM", 0))
                    low_count = int(sim_summary["risk_counts"].get("LOW", 0))
                    st.markdown(
                        f"**{selected_scenario} produced {high_count} high-risk, "
                        f"{medium_count} moderate-risk, and {low_count} low-risk result(s) "
                        f"out of {sim_summary['total_simulated']} simulated people.**"
                    )
                    if high_count:
                        st.warning("High-risk cases may come from the model estimate or from safety rules when red flags are detected.")
                    else:
                        st.success("No high-risk cases were generated in this scenario.")

                    export_csv = df_batch_records.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "Download scenario report",
                        data=export_csv,
                        file_name=f"{sim_summary['batch_id']}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                    # Risk classification breakdown
                    counts_df = df_batch_records["predicted_risk"].value_counts().reset_index()
                    counts_df.columns = ["Risk Level", "Count"]
                    colors_map = {'LOW': '#2ecc71', 'MEDIUM': '#f1c40f', 'HIGH': '#e74c3c'}
                    
                    fig_sim_pie = px.pie(
                        counts_df, 
                        values='Count', 
                        names='Risk Level', 
                        hole=0.4,
                        color='Risk Level',
                        color_discrete_map=colors_map,
                        title="Risk distribution in simulated group"
                    )
                    fig_sim_pie.update_layout(height=250, margin=dict(t=40, b=20, l=10, r=10))
                    st.plotly_chart(fig_sim_pie, use_container_width=True)

                    high_risk_cases = df_batch_records[df_batch_records["predicted_risk"] == "HIGH"].copy()
                    if not high_risk_cases.empty:
                        st.markdown("**High-risk case review**")
                        high_risk_cases["Safety Override"] = high_risk_cases["safety_override_applied"].apply(
                            lambda val: "Yes" if int(val) == 1 else "No"
                        )
                        high_risk_view = high_risk_cases.rename(columns={
                            "patient_name": "Person / ID",
                            "ml_risk": "Model Risk",
                            "predicted_risk": "Final Risk",
                            "body_temp": "Body Temp (C)",
                            "heat_index": "Heat Index (C)",
                            "heart_rate": "Heart Rate",
                            "water_intake": "Hydration (L)",
                        })
                        st.dataframe(
                            high_risk_view[[
                                "Person / ID", "Model Risk", "Final Risk", "Body Temp (C)", "Heat Index (C)",
                                "Heart Rate", "Hydration (L)", "Safety Override"
                            ]].head(10),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    # Vitals boxplot
                    if df_batch_records["predicted_risk"].nunique() >= 2:
                        fig_box = px.box(
                            df_batch_records, 
                            x="predicted_risk", 
                            y="body_temp", 
                            color="predicted_risk",
                            color_discrete_map=colors_map,
                            title="Body temperature by risk group",
                            labels={
                                "predicted_risk": "Risk",
                                "body_temp": "Body Temperature (C)"
                            }
                        )
                        fig_box.update_layout(height=250, margin=dict(t=40, b=20, l=10, r=10))
                        st.plotly_chart(fig_box, use_container_width=True)
                    else:
                        st.info("Body-temperature comparison is hidden because this run generated only one risk group.")

                    fig_heat_scatter = px.scatter(
                        df_batch_records,
                        x="heat_index",
                        y="body_temp",
                        color="predicted_risk",
                        size="confidence",
                        hover_data=["patient_name", "water_intake", "heart_rate", "confusion"],
                        color_discrete_map=colors_map,
                        title="Heat exposure vs body temperature",
                        labels={
                            "heat_index": "Heat Index (C)",
                            "body_temp": "Body Temperature (C)",
                            "predicted_risk": "Risk",
                            "confidence": "Confidence",
                            "patient_name": "Person / ID",
                            "water_intake": "Hydration (L)",
                            "heart_rate": "Heart Rate",
                            "confusion": "Confusion"
                        }
                    )
                    fig_heat_scatter.update_layout(height=280, margin=dict(t=40, b=20, l=10, r=10))
                    st.plotly_chart(fig_heat_scatter, use_container_width=True)

                    symptom_cols = ["dizziness", "headache", "muscle_cramps", "nausea", "confusion"]
                    symptom_rates = (
                        df_batch_records.groupby("predicted_risk")[symptom_cols]
                        .mean()
                        .reindex(["LOW", "MEDIUM", "HIGH"])
                        .fillna(0)
                        * 100
                    )
                    symptom_rates = symptom_rates.rename(columns={
                        "dizziness": "Dizziness",
                        "headache": "Headache",
                        "muscle_cramps": "Muscle Cramps",
                        "nausea": "Nausea",
                        "confusion": "Confusion"
                    })
                    fig_sim_symptoms = px.imshow(
                        symptom_rates,
                        labels=dict(x="Symptom", y="Risk Level", color="% Present"),
                        text_auto=".1f",
                        color_continuous_scale="YlOrRd",
                        aspect="auto",
                        title="Symptoms by simulated risk group"
                    )
                    fig_sim_symptoms.update_layout(height=260, margin=dict(t=40, b=20, l=10, r=10))
                    st.plotly_chart(fig_sim_symptoms, use_container_width=True)
                    with st.expander("Scenario batch details", expanded=False):
                        rule_engine_version = "N/A"
                        if "rule_engine_version" in df_batch_records.columns and not df_batch_records["rule_engine_version"].dropna().empty:
                            rule_engine_version = df_batch_records["rule_engine_version"].dropna().iloc[0]
                        elif sim_summary.get("records"):
                            rule_engine_version = sim_summary["records"][0].get("rule_engine_version", "N/A")
                        st.write(f"**Batch ID:** {sim_summary['batch_id']}")
                        st.write(f"**Rule engine:** {rule_engine_version}")
                        st.write(f"**Demo seed:** {sim_summary.get('random_seed', 'Randomized')}")
                        st.write("Safety-adjusted final risk is used for these charts and reports.")
        else:
            st.info("Choose a scenario and click 'Run Scenario' to display simulated group results here.")

# ================= TAB 4: SAFETY PORTAL =================
with tab_guide:
    render_safety_protocols()
