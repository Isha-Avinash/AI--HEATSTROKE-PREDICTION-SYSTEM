import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import project modules
from database import init_db, save_record, get_all_records, clear_database, get_records_by_batch
from model import predict_risk_ml, get_feature_importances, get_model_metadata, get_confusion_matrix
from weather import get_live_weather
from model_trainer import calculate_heat_index, train_and_save_model
from ui_helpers import inject_custom_css, speak_browser, get_health_recommendations, get_first_aid_guide
from symptom_analyzer import extract_symptoms
from risk_tracker import get_patient_timeline, detect_risk_trend
from simulator import run_cohort_simulation

# Initialize DB on load
init_db()

# Streamlit App Configurations
st.set_page_config(
    page_title="AI Heatstroke Prediction & Diagnostics",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject modern Custom CSS definitions
inject_custom_css()

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    
    # Simple branding/info
    st.info("💡 **Clinical Tip:** Heatstroke occurs when body temperature climbs above 40°C, leading to central nervous system failure. Early detection of symptoms saves lives.")
    
    st.markdown("---")
    
    # Model Registry Panel (Phase 5)
    st.markdown("### 🧠 Model Registry")
    metadata = get_model_metadata()
    metrics = metadata.get("metrics", {})
    st.markdown(f"**Model Class:** `{metadata.get('model_type', 'N/A')}`")
    st.markdown(f"**Trained On:** `{metadata.get('training_date', 'N/A')}`")
    
    col_met1, col_met2 = st.columns(2)
    col_met1.metric("CV Accuracy", f"{metrics.get('accuracy', 0.0):.1f}%")
    col_met2.metric("Macro F1", f"{metrics.get('f1_score', 0.0):.1f}%")
    
    if st.button("🔄 Retrain ML Pipeline", help="Regenerates synthetic clinical data (5,000 samples) and retrains all classifier models"):
        with st.spinner("Retraining classifier..."):
            train_and_save_model()
            st.success("Classifier successfully retrained!")
            st.rerun()
            
    st.markdown("---")
    
    # Data Export and Management (Phase 5)
    st.markdown("### 💾 Data Management")
    records = get_all_records()
    if records:
        df_export = pd.DataFrame(records)
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Logs as CSV",
            data=csv_data,
            file_name=f"heatstroke_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Download all sqlite patient assessment logs"
        )
        
    if st.button("⚠️ Clear Assessment Logs", help="Remove all historical runs from SQLite"):
        clear_database()
        st.success("All logs cleared successfully!")
        st.rerun()

# ================= APP HEADER =================
st.markdown("<h1 class='app-title'>🔥 Clinical Heatstroke AI Predictor</h1>", unsafe_allow_html=True)
st.markdown("<p class='app-subtitle'>Real-time diagnostic screening using local Ensemble Machine Learning, Natural Language Processing, & Apparent Temperature Analysis</p>", unsafe_allow_html=True)

# Define Tabs
tab_pred, tab_analytics, tab_sim, tab_guide = st.tabs([
    "🔮 AI Diagnostic Screening", 
    "📊 Data Science & ML Analytics", 
    "🔬 Simulation Lab",
    "📘 Medical Safety Portal"
])

# ================= TAB 1: AI PREDICTOR =================
with tab_pred:
    st.markdown("### 🩺 Diagnostic Input Panel")
    st.write("Complete the details below or describe symptoms in natural language to generate a real-time clinical heatstroke risk assessment.")
    
    # NLP Input Block (Phase 2)
    with st.container(border=True):
        st.markdown("<h4>📝 Describe Symptoms (Natural Language)</h4>", unsafe_allow_html=True)
        nlp_text = st.text_area(
            "Describe how you feel (e.g. 'I feel extremely dizzy and nauseous with a throbbing headache, and my calves are cramping up'):", 
            placeholder="Type clinical descriptions here...",
            key="nlp_description_input"
        )
        if st.button("Parse Symptoms via NLP", help="Runs semantic symptom mapping using local SentenceTransformers"):
            if nlp_text.strip() != "":
                with st.spinner("Analyzing text using local transformer model..."):
                    nlp_res = extract_symptoms(nlp_text)
                    st.session_state.nlp_flags = nlp_res["flags"]
                    st.session_state.nlp_scores = nlp_res["scores"]
                    st.success("Symptoms successfully parsed! Clinical checkboxes have been updated below.")
            else:
                st.warning("Please type a description of your symptoms first.")
                
    # Get values populated from NLP if available
    nlp_flags = st.session_state.get("nlp_flags", {})
    diz_val = bool(nlp_flags.get("Dizziness", False))
    head_val = bool(nlp_flags.get("Headache", False))
    cramp_val = bool(nlp_flags.get("MuscleCramps", False))
    nausea_val = bool(nlp_flags.get("Nausea", False))
    conf_val = bool(nlp_flags.get("Confusion", False))
    
    # 2-column input layout: Left = Environmental, Right = Physiological
    col_env, col_phys = st.columns(2)
    
    with col_env:
        with st.container(border=True):
            st.markdown("<h4>🌍 1. Environmental Conditions</h4>", unsafe_allow_html=True)
            
            # Weather Lookup Widget
            city_input = st.text_input("📍 Auto-Fetch Weather (City)", "Delhi", help="Enter a city name to populate local temperature and humidity instantly.")
            if st.button("Fetch Live Weather"):
                with st.spinner("Retrieving weather conditions..."):
                    weather_data = get_live_weather(city_input)
                    if weather_data["success"]:
                        st.session_state.temp = weather_data["temp"]
                        st.session_state.humidity = weather_data["humidity"]
                        st.success(f"Loaded {weather_data['city']}: {weather_data['temp']}°C, {weather_data['humidity']}% Humidity ({weather_data['description']})")
                    else:
                        st.warning("Could not reach weather API. Falling back to manual values.")
            
            # Environmental sliders (initialize using session state if fetched)
            default_temp = st.session_state.get("temp", 35.0)
            default_humidity = st.session_state.get("humidity", 50.0)
            
            outdoor_temp = st.slider("Ambient Temperature (°C)", 15.0, 50.0, float(default_temp), 0.1, help="Actual shade temperature outside.")
            humidity = st.slider("Relative Humidity (%)", 5.0, 100.0, float(default_humidity), 1.0, help="Humidity slows down sweat evaporation.")
            
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
            st.markdown("<h4>👤 2. Physiological Parameters</h4>", unsafe_allow_html=True)
            
            # Demographics
            pat_name = st.text_input("Patient Name / ID", "Anonymous")
            
            col_dem1, col_dem2 = st.columns(2)
            with col_dem1:
                age = st.number_input("Age (Years)", 1, 120, 28)
                weight = st.number_input("Weight (kg)", 10.0, 200.0, 70.0, 0.5)
            with col_dem2:
                height = st.number_input("Height (m)", 0.5, 2.5, 1.75, 0.01)
                heart_rate = st.slider("Heart Rate (bpm)", 50, 200, 80, help="Resting or active pulse.")
                
            bmi = round(weight / (height ** 2), 2) if height > 0 else 0.0
            st.write(f"**Body Mass Index (BMI):** `{bmi:.2f}`")
            
            st.markdown("---")
            
            # Body Vitals
            body_temp = st.slider("Internal Body Temperature (°C)", 35.5, 43.0, 37.0, 0.1, help="Measured orally, tympanically, or rectally. Over 39°C points to hyperthermia.")
            water_intake = st.slider("Today's Hydration Intake (Liters)", 0.0, 6.0, 2.0, 0.1, help="Recommended intake is > 2.5L in heat.")
            
            # Symptoms Checkbox
            st.markdown("**Active Clinical Symptoms:**")
            col_sym1, col_sym2 = st.columns(2)
            with col_sym1:
                dizziness = st.checkbox("Severe Dizziness / Vertigo", value=diz_val)
                headache = st.checkbox("Throbbing Headache", value=head_val)
                muscle_cramps = st.checkbox("Muscle Cramps / Spasms", value=cramp_val)
            with col_sym2:
                nausea = st.checkbox("Nausea / Vomiting", value=nausea_val)
                confusion = st.checkbox("Confusion / Delirium", value=conf_val)

    # ACTION BUTTON
    st.markdown("---")
    if st.button("🔥 RUN MACHINE LEARNING DIAGNOSIS", use_container_width=True):
        diz_int = 1 if dizziness else 0
        head_int = 1 if headache else 0
        cramp_int = 1 if muscle_cramps else 0
        nausea_int = 1 if nausea else 0
        conf_int = 1 if confusion else 0
        
        # Run ML model inference with 12 features
        result = predict_risk_ml(
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
        
        risk = result["predicted_risk"]
        confidence = result["confidence"]
        heat_index_val = result["heat_index"]
        probabilities = result["probabilities"]
        
        # Save assessment to SQLite database with new columns
        save_record(
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
            predicted_risk=risk,
            confidence=confidence,
            muscle_cramps=cramp_int,
            nausea=nausea_int,
            confusion=conf_int
        )
        
        # Trigger client-side browser text-to-speech voice alert!
        alert_msg = f"Alert. Diagnostic assessment completed. Predicted heatstroke risk is {risk}."
        if risk == "HIGH":
            alert_msg = "Critical Warning. High heatstroke risk detected. Initiate emergency cooling protocols."
        elif risk == "MEDIUM":
            alert_msg = "Attention. Moderate risk detected. Stop activity and hydrate immediately."
            
        speak_browser(alert_msg)
        
        # Display Results Panel
        st.markdown("### 🧬 Diagnostic Results")
        col_res1, col_res2 = st.columns([1, 1.2])
        
        with col_res1:
            with st.container(border=True):
                st.markdown("<h4>🧠 AI Classifier Probability</h4>", unsafe_allow_html=True)
                
                # Map colors for the gauge chart based on prediction risk
                gauge_color = "#2ecc71" if risk == "LOW" else "#f1c40f" if risk == "MEDIUM" else "#e74c3c"
                
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
                st.write("**Prediction Class Breakdown:**")
                st.progress(probabilities["LOW"] / 100.0, text=f"🟢 Low Risk Probability: {probabilities['LOW']}%")
                st.progress(probabilities["MEDIUM"] / 100.0, text=f"🟡 Medium Risk Probability: {probabilities['MEDIUM']}%")
                st.progress(probabilities["HIGH"] / 100.0, text=f"🔴 High Risk Probability: {probabilities['HIGH']}%")
            
        with col_res2:
            # Custom clinical actions card
            recs = get_health_recommendations(risk, body_temp, water_intake, bmi)
            
            # Render risk banner in a single HTML block
            banner_style = "emergency-box" if risk == "HIGH" else "glass-card"
            badge_class = f"badge badge-{recs['indicator']}"
            
            actions_li = "".join([f"<li>{act.replace('**', '<strong>', 1).replace('**', '</strong>', 1)}</li>" for act in recs['actions']])
            
            html_card = f"""
            <div class='{banner_style}'>
                <h3 style='margin-top:0; color:inherit;'>{recs['title']} <span class='{badge_class}'>{risk} RISK</span></h3>
                <p style='color:inherit;'>{recs['summary']}</p>
                <hr style='border: 0; border-top: 1px solid rgba(255,255,255,0.15); margin: 1rem 0;'>
                <strong style='color:inherit;'>Recommended Action Steps:</strong>
                <ul style='margin-top: 0.5rem; padding-left: 1.2rem; color:inherit;'>
                    {actions_li}
                </ul>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)

# ================= TAB 2: DATA SCIENCE & ML ANALYTICS =================
with tab_analytics:
    st.markdown("### 📊 Cohort Analytics & ML Explainability Dashboard")
    st.write("This dashboard queries the SQLite database to analyze historical screenings, examine model metrics, and track trends.")
    
    records = get_all_records()
    
    if not records:
        st.warning("📂 **No Assessment Logs Available Yet.** Generate sample assessments in the 'AI Diagnostic Screening' tab to view charts.")
    else:
        df_logs = pd.DataFrame(records)
        df_logs = df_logs.sort_values("timestamp")
        df_logs['Run'] = range(1, len(df_logs) + 1)
        
        # 1. Individual Time-Series tracking (Phase 3)
        st.markdown("#### ⏳ Individual Patient Risk Timeline (Time-Series)")
        patient_names = [p for p in df_logs["patient_name"].unique() if p != "Anonymous"]
        if patient_names:
            col_t1, col_t2 = st.columns([1, 2])
            with col_t1:
                selected_patient = st.selectbox("Select Patient to view history:", patient_names)
                timeline = get_patient_timeline(selected_patient)
                trend = detect_risk_trend(timeline)
                
                if trend["status"] == "CRITICAL ESCALATION":
                    st.error(trend["message"])
                elif "RISK ESCALATING" in trend["status"] or "TEMP RISING" in trend["status"]:
                    st.warning(trend["message"])
                else:
                    st.success(trend["message"])
            with col_t2:
                if len(timeline) >= 1:
                    df_time = pd.DataFrame(timeline)
                    df_time['timestamp'] = pd.to_datetime(df_time['timestamp'])
                    df_time = df_time.sort_values("timestamp")
                    
                    fig_time = px.line(
                        df_time, 
                        x="timestamp", 
                        y="body_temp", 
                        title=f"Vitals & Heat Index History for {selected_patient}",
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
        else:
            st.info("💡 Enter non-Anonymous patient names in Tab 1 to track personal time-series risk trends.")
            
        st.markdown("---")
        
        # 2. KPIs Row
        st.markdown("#### 📈 Key Metrics Summary")
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        total_runs = len(df_logs)
        high_risk_runs = len(df_logs[df_logs["predicted_risk"] == "HIGH"])
        high_risk_percentage = round((high_risk_runs / total_runs) * 100, 1)
        avg_body_temp = round(df_logs["body_temp"].mean(), 2)
        avg_water = round(df_logs["water_intake"].mean(), 2)
        
        kpi_col1.metric("Total Assessments Logged", f"{total_runs}", "runs")
        kpi_col2.metric("Critical High Risk Cases", f"{high_risk_runs}", f"{high_risk_percentage}% of total", delta_color="inverse" if high_risk_percentage > 15 else "normal")
        kpi_col3.metric("Average Patient Body Temp", f"{avg_body_temp} °C", "Normal is 37°C")
        kpi_col4.metric("Avg Patient Hydration", f"{avg_water} Liters", "Target: > 2.5L")
        
        st.markdown("---")
        
        # 3. Charts Row 1: Risk Distribution vs Vitals Trends
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            with st.container(border=True):
                st.markdown("<h5>🟢 Risk Classification Distribution</h5>", unsafe_allow_html=True)
                risk_counts = df_logs["predicted_risk"].value_counts().reset_index()
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
                st.markdown("<h5>📈 Internal Vitals Trend (Body Temp vs Heart Rate)</h5>", unsafe_allow_html=True)
                fig_trend = px.line(
                    df_logs, 
                    x="Run", 
                    y=["body_temp", "heart_rate"], 
                    labels={"value": "Vital Measure", "variable": "Indicator"},
                    markers=True,
                    color_discrete_sequence=["#e74c3c", "#3498db"]
                )
                fig_trend.update_layout(height=280, margin=dict(t=20, b=20, l=10, r=10))
                st.plotly_chart(fig_trend, use_container_width=True)
            
        # 4. Charts Row 2: ML Feature Importance vs Confusion Matrix (Phase 1)
        chart_col3, chart_col4 = st.columns(2)
        
        with chart_col3:
            with st.container(border=True):
                st.markdown("<h5>🧠 Model Explainability: Feature Importance</h5>", unsafe_allow_html=True)
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
            with st.container(border=True):
                st.markdown("<h5>🌀 Confusion Matrix</h5>", unsafe_allow_html=True)
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
                    st.info("Confusion matrix data unavailable.")
                    
        # 5. Data Logs Table
        st.markdown("#### 📋 Data Log Record")
        st.dataframe(
            df_logs.sort_values("timestamp", ascending=False)[["timestamp", "patient_name", "age", "calculated_bmi", "body_temp", "water_intake", "heat_index", "predicted_risk", "confidence"]],
            use_container_width=True
        )

# ================= TAB 3: SIMULATION LAB (Phase 4) =================
with tab_sim:
    st.markdown("### 🔬 Population Simulation Lab")
    st.write("Run batch screening simulations for cohorts of patients exposed to distinct environmental microclimates.")
    
    col_sim_c1, col_sim_c2 = st.columns([1, 1.2])
    
    with col_sim_c1:
        with st.container(border=True):
            st.markdown("<h4>⚙️ Simulation Controls</h4>", unsafe_allow_html=True)
            scenario_choice = st.selectbox(
                "Select Climate Scenario:", 
                ["Heatwave Delhi", "Monsoon Mumbai", "Normal Bangalore"],
                key="sim_scenario_select"
            )
            cohort_size = st.slider("Cohort Size (Number of Patients):", 10, 500, 100, key="sim_cohort_slider")
            
            if st.button("🚀 Run Cohort Simulation", use_container_width=True):
                with st.spinner(f"Simulating {cohort_size} patients under {scenario_choice}..."):
                    sim_summary = run_cohort_simulation(cohort_size, scenario_choice)
                    st.session_state.sim_summary = sim_summary
                    st.session_state.sim_scenario = scenario_choice
                    st.success(f"Simulation completed! Batch ID: {sim_summary['batch_id']}")
                    
    with col_sim_c2:
        sim_summary = st.session_state.get("sim_summary", None)
        selected_scenario = st.session_state.get("sim_scenario", "")
        if sim_summary:
            with st.container(border=True):
                st.markdown(f"<h4>📊 Simulation Results: {selected_scenario}</h4>", unsafe_allow_html=True)
                
                # KPIs
                col_sk1, col_sk2 = st.columns(2)
                col_sk1.metric("Avg Ambient Heat Index", f"{sim_summary['avg_heat_index']} °C")
                col_sk2.metric("Avg Body Temperature", f"{sim_summary['avg_body_temp']} °C")
                
                # Plotly risk distribution pie chart for this batch
                df_batch_records = pd.DataFrame(get_records_by_batch(sim_summary["batch_id"]))
                
                if not df_batch_records.empty:
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
                        title="Risk Level Distribution in Simulated Cohort"
                    )
                    fig_sim_pie.update_layout(height=250, margin=dict(t=40, b=20, l=10, r=10))
                    st.plotly_chart(fig_sim_pie, use_container_width=True)
                    
                    # Vitals boxplot
                    fig_box = px.box(
                        df_batch_records, 
                        x="predicted_risk", 
                        y="body_temp", 
                        color="predicted_risk",
                        color_discrete_map=colors_map,
                        title="Body Temperature Distribution by Risk Group"
                    )
                    fig_box.update_layout(height=250, margin=dict(t=40, b=20, l=10, r=10))
                    st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("💡 Choose a scenario and click 'Run Cohort Simulation' to display simulated cohort analytics here.")

# ================= TAB 4: SAFETY PORTAL =================
with tab_guide:
    st.markdown("### 📘 Clinical Information & Emergency First Aid")
    st.write("Understand the key medical definitions and cooling procedures to combat heat emergencies.")
    
    guides = get_first_aid_guide()
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Heat Exhaustion Guide Card
        symptoms_li = "".join([f"<li>{sym}</li>" for sym in guides["Heat Exhaustion"]["Symptoms"]])
        first_aid_li = "".join([f"<li>👉 {fa}</li>" for fa in guides["Heat Exhaustion"]["FirstAid"]])
        
        g1_html = f"""
        <div class='glass-card'>
            <h3 style='margin-top:0; color:inherit;'>🟡 Heat Exhaustion</h3>
            <p>Heat exhaustion is the body's response to an excessive loss of water and salt, usually through sweating.</p>
            <strong>Key Identifying Symptoms:</strong>
            <ul style='padding-left: 1.2rem; margin-top: 0.5rem;'>
                {symptoms_li}
            </ul>
            <hr style='border:0; border-top: 1px solid rgba(255,255,255,0.1); margin: 1rem 0;'>
            <strong>First Aid Interventions:</strong>
            <ul style='list-style: none; padding-left: 0; margin-top: 0.5rem; line-height: 1.6;'>
                {first_aid_li}
            </ul>
        </div>
        """
        st.markdown(g1_html, unsafe_allow_html=True)
        
    with col_g2:
        # Heat Stroke Guide Card
        symptoms_li = "".join([f"<li>{sym}</li>" for sym in guides["Heat Stroke (Medical Emergency)"]["Symptoms"]])
        first_aid_li = "".join([f"<li>🚨 {fa}</li>" for fa in guides["Heat Stroke (Medical Emergency)"]["FirstAid"]])
        
        g2_html = f"""
        <div class='emergency-box'>
            <h3 style='margin-top:0; color:white;'>🔴 Heat Stroke (Critical Emergency)</h3>
            <p style='color:white;'>Heatstroke is a life-threatening medical emergency. The body's heat-regulating system fails, and body temperature spikes to critical levels.</p>
            <strong style='color:white;'>Key Identifying Symptoms:</strong>
            <ul style='padding-left: 1.2rem; margin-top: 0.5rem; color:white;'>
                {symptoms_li}
            </ul>
            <hr style='border:0; border-top: 1px solid rgba(255,255,255,0.2); margin: 1rem 0;'>
            <strong style='color:white;'>Immediate First Aid Interventions:</strong>
            <ul style='list-style: none; padding-left: 0; margin-top: 0.5rem; line-height: 1.6; color:white;'>
                {first_aid_li}
            </ul>
        </div>
        """
        st.markdown(g2_html, unsafe_allow_html=True)