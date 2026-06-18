import streamlit as st
import streamlit.components.v1 as components
from html import escape
import pandas as pd

def inject_custom_css():
    """Injects high-end, responsive custom styling into Streamlit."""
    custom_css = """
    <style>
    /* Premium fonts and background styling */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Elegant Title and Header styling */
    .app-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF4B2B 0%, #FF8C00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
        filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.1));
    }
    
    .app-subtitle {
        font-size: 1.1rem;
        color: #888888;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Style the native Streamlit containers to look like Glassmorphic Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25) !important;
        margin-bottom: 1.5rem !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.35) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
    }

    /* Glassmorphic HTML Cards (for static custom HTML layout) */
    .glass-card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25) !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Recommendation badges */
    .badge {
        display: inline-block;
        padding: 0.25em 0.6em;
        font-size: 75%;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 10rem;
    }
    
    .badge-low { background-color: #d4edda; color: #155724; }
    .badge-medium { background-color: #fff3cd; color: #856404; }
    .badge-high { background-color: #f8d7da; color: #721c24; }
    
    /* Emergency alert container */
    .emergency-box {
        background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%) !important;
        color: white !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 24px rgba(255, 65, 108, 0.3) !important;
        margin-bottom: 1.5rem !important;
        border: none !important;
    }

    .emergency-box h3, .emergency-box p, .emergency-box strong, .emergency-box li, .emergency-box ul {
        color: white !important;
    }

    .screening-note {
        border-left: 4px solid #3498db;
        background: rgba(52, 152, 219, 0.10);
        padding: 0.85rem 1rem;
        border-radius: 8px;
        margin-bottom: 1.25rem;
        color: inherit;
    }

    .factor-chip {
        display: inline-block;
        padding: 0.35rem 0.65rem;
        margin: 0.2rem 0.25rem 0.2rem 0;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        font-size: 0.9rem;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def speak_browser(text):
    """
    Executes client-side Web Speech Synthesis API inside the user's browser.
    Completely free and runs asynchronously.
    """
    clean_text = text.replace('"', '\\"').replace("'", "\\'")
    js_code = f"""
    <script>
    if ('speechSynthesis' in window) {{
        // Cancel any ongoing speeches
        window.speechSynthesis.cancel();
        
        const utter = new SpeechSynthesisUtterance("{clean_text}");
        utter.volume = 1.0;
        utter.rate = 1.0;
        utter.pitch = 1.0;
        
        // Find a suitable English natural voice if available
        const voices = window.speechSynthesis.getVoices();
        const engVoice = voices.find(v => v.lang.includes('en'));
        if (engVoice) utter.voice = engVoice;
        
        window.speechSynthesis.speak(utter);
    }}
    </script>
    """
    components.html(js_code, height=0, width=0)

def get_health_recommendations(risk_level, temp, water, bmi):
    """Returns clinical, actionable insights based on prediction results."""
    rec = {
        "LOW": {
            "title": "✅ Health Status: Stable & Safe",
            "summary": "Your parameters show no immediate risk of heatstroke. Maintain healthy hydration and thermal practices.",
            "actions": [
                "**Hydration Target**: Continue drinking at least 2.5 - 3.0 Liters of water daily.",
                "**Activity Check**: Normal outdoor activity is acceptable, but take brief shade intervals if weather indices rise.",
                "**Nutrition**: Consume electrolyte-rich foods (fruits, yogurt) to support water absorption."
            ],
            "indicator": "low"
        },
        "MEDIUM": {
            "title": "⚠️ Health Status: Moderate Heat Strain",
            "summary": "Your metrics show signs of mild heat exhaustion or insufficient hydration under hot ambient conditions. Immediate precautions required.",
            "actions": [
                "**Hydration Warning**: Drink 1-2 glasses of water or electrolyte solution *immediately*. Avoid caffeine or alcohol.",
                "**Cool Down**: Rest in an air-conditioned room or in the direct path of a fan. Loosen tight clothing.",
                "**Symptom Patrol**: If dizziness or headache worsens, apply damp cloths to your face and back of neck."
            ],
            "indicator": "medium"
        },
        "HIGH": {
            "title": "🚨 Health Status: High Heatstroke Risk (Critical Warning)",
            "summary": "CRITICAL! High likelihood of exertional or classic heat stroke. Body thermoregulation is failing. Action is required to prevent heat injury.",
            "actions": [
                "**Call Emergency Services**: Seek immediate medical attention if body temp exceeds 40°C or confusion is present.",
                "**Active Cooling**: Apply ice packs or cold damp towels to axilla (armpits), groin, and neck.",
                "**Absolute Rest**: Stop all physical exertion immediately. Elevate legs slightly to prevent shock.",
                "**Hydration (Caution)**: Do NOT force-feed water if the person is semi-conscious, vomiting, or highly disoriented."
            ],
            "indicator": "high"
        }
    }
    return rec.get(risk_level, rec["LOW"])

def get_screening_summary(risk_level):
    """Returns user-facing summary language for the screening result."""
    summaries = {
        "LOW": {
            "label": "Low estimated risk",
            "tone": "The entered values look relatively stable right now. Continue monitoring if heat exposure continues.",
            "next_step": "Keep hydration steady, avoid unnecessary heat exposure, and reassess if symptoms appear."
        },
        "MEDIUM": {
            "label": "Moderate estimated risk",
            "tone": "The entered values suggest heat strain. This is a warning state, especially if symptoms are worsening.",
            "next_step": "Stop exertion, move to a cooler place, hydrate, and reassess after cooling."
        },
        "HIGH": {
            "label": "High estimated risk",
            "tone": "The entered values match a high-risk heat illness pattern. Treat this as urgent.",
            "next_step": "Begin active cooling and seek emergency medical help if confusion, collapse, or very high body temperature is present."
        }
    }
    return summaries.get(risk_level, summaries["LOW"])

def get_risk_drivers(body_temp, water_intake, heart_rate, heat_index, symptoms):
    """Builds explainable, rule-based drivers for the ML screening result."""
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
        "confusion": "Confusion/delirium"
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
        "protective": protective[:3]
    }

def render_result_overview(risk, confidence, body_temp, water_intake, heart_rate, heat_index, bmi):
    """Renders compact result metrics above the detailed explanation."""
    summary = get_screening_summary(risk)
    risk_class = risk.lower()

    st.markdown(
        f"""
        <div class='glass-card'>
            <h3 style='margin-top:0;'>{escape(summary["label"])} <span class='badge badge-{risk_class}'>{escape(risk)} RISK</span></h3>
            <p>{escape(summary["tone"])}</p>
            <p><strong>Suggested next step:</strong> {escape(summary["next_step"])}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Model Confidence", f"{confidence:.1f}%")
    m2.metric("Body Temp", f"{body_temp:.1f} C")
    m3.metric("Heat Index", f"{heat_index:.1f} C")
    m4.metric("Hydration", f"{water_intake:.1f} L")

    st.caption(f"BMI: {bmi:.2f} | Heart rate: {heart_rate} bpm | This is a screening aid, not a medical diagnosis.")

def render_risk_driver_panel(drivers):
    """Renders explanation chips and driver/protective-factor lists."""
    with st.container(border=True):
        st.markdown("<h4>Why this estimate?</h4>", unsafe_allow_html=True)

        if drivers["drivers"]:
            st.markdown("**Main risk drivers detected:**")
            for title, detail in drivers["drivers"]:
                st.markdown(f"- **{title}:** {detail}")
        else:
            st.success("No major risk drivers were detected from the entered values.")

        if drivers["protective"]:
            st.markdown("**Stabilizing factors:**")
            for title, detail in drivers["protective"]:
                st.markdown(f"- **{title}:** {detail}")

def render_model_explanation_panel(explanation):
    """Renders user-facing factor guidance with advanced model details tucked away."""
    with st.container(border=True):
        st.markdown("<h4>Key factors behind this result</h4>", unsafe_allow_html=True)

        top_factors = explanation.get("top_factors", [])
        if top_factors:
            st.markdown("**What appears to be influencing this screening:**")
            for item in top_factors:
                st.markdown(f"- **{item['label']}:** meaningful signal in this assessment.")
        else:
            st.success("No strong risk-driving factors were found in this input.")

        targets = explanation.get("improvement_targets", [])
        if targets:
            st.markdown("**Most useful changes to try next:**")
            for target in targets:
                st.markdown(f"- {target}")

        all_factors = explanation.get("all_factors", [])
        if top_factors or all_factors:
            with st.expander("Advanced model details"):
                st.caption(explanation.get("method_note", "Local explanation based on trained feature importances."))

                if top_factors:
                    st.markdown("**Top model-weighted factors:**")
                    max_influence = max(item["influence"] for item in top_factors) or 1.0
                    for item in top_factors:
                        score = item["influence"] / max_influence
                        st.progress(
                            score,
                            text=(
                                f"{item['label']} | contribution {item['influence']:.3f} "
                                f"| risk signal {item['risk_pressure']:.2f}"
                            )
                        )

                if not all_factors:
                    return

                df = pd.DataFrame(all_factors)
                df = df.rename(columns={
                    "label": "Factor",
                    "model_weight": "Model Weight",
                    "risk_pressure": "Risk Signal",
                    "influence": "Contribution"
                })
                st.dataframe(
                    df[["Factor", "Model Weight", "Risk Signal", "Contribution"]],
                    use_container_width=True,
                    hide_index=True
                )

def render_nlp_review_panel(nlp_result):
    """Renders detected symptoms with accept/reject controls."""
    if not nlp_result:
        return {}

    flags = nlp_result.get("flags", {})
    scores = nlp_result.get("scores", {})
    matches = nlp_result.get("matches", {})
    method_label = nlp_result.get("method_label", "Symptom parser")
    message = nlp_result.get("message", "Review detected symptoms before continuing.")

    with st.container(border=True):
        labels = {
            "Dizziness": "Dizziness / vertigo",
            "Headache": "Headache",
            "MuscleCramps": "Muscle cramps",
            "Nausea": "Nausea / vomiting",
            "Confusion": "Confusion / delirium"
        }
        detected_labels = [labels[symptom] for symptom in labels if flags.get(symptom)]

        st.markdown("<h4>Confirm detected symptoms</h4>", unsafe_allow_html=True)
        if detected_labels:
            st.success("Suggested from description: " + ", ".join(detected_labels))
        else:
            st.info("No tracked symptoms were confidently detected. You can still select symptoms manually.")

        st.write("Confirm what should be included in the screening:")

        accepted_flags = {}
        cols = st.columns(2)
        for idx, symptom in enumerate(labels.keys()):
            col = cols[idx % 2]
            detected = bool(flags.get(symptom, 0))

            with col:
                accepted = st.checkbox(
                    labels[symptom],
                    value=detected,
                    key=f"nlp_accept_{symptom}",
                    help="Use this symptom in the screening result."
                )
                accepted_flags[symptom] = 1 if accepted else 0

        with st.expander("Show detection details"):
            st.caption(f"{method_label}: {message}")
            for symptom in labels:
                score = float(scores.get(symptom, 0.0))
                match_text = ", ".join(matches.get(symptom, [])) or "No close phrase match"
                st.progress(
                    min(score, 1.0),
                    text=f"{labels[symptom]}: confidence {score:.2f} | closest match: {match_text}"
                )

        return accepted_flags

def render_emergency_checklist(risk):
    """Renders an actionable checklist for urgent heat illness handling."""
    if risk != "HIGH":
        return

    with st.container(border=True):
        st.markdown("#### Emergency Cooling Checklist")
        st.error("High-risk screening result. If the person is confused, collapsing, or has very high body temperature, seek emergency medical help now.")
        st.checkbox("Move the person to shade or an air-conditioned area.", key="cooling_step_move")
        st.checkbox("Stop all exertion and loosen tight clothing.", key="cooling_step_rest")
        st.checkbox("Apply cool wet cloths or ice packs to neck, armpits, and groin.", key="cooling_step_ice")
        st.checkbox("Do not force fluids if the person is confused, vomiting, or not fully alert.", key="cooling_step_fluids")

def get_first_aid_guide():
    """Returns details for the Emergency Info Portal."""
    return {
        "Heat Exhaustion": {
            "Symptoms": ["Heavy sweating", "Paleness", "Muscle cramps", "Tiredness/Weakness", "Dizziness", "Headache", "Nausea or vomiting", "Fainting"],
            "FirstAid": [
                "Move to a cool, shaded, or air-conditioned space.",
                "Loosen or remove excess clothing.",
                "Cool the body by spraying with cool water or applying cool, wet cloths.",
                "Sip cool fluids (water, sports drinks, electrolyte formulas).",
                "Seek medical care if symptoms worsen or do not improve within 1 hour."
            ]
        },
        "Heat Stroke (Medical Emergency)": {
            "Symptoms": ["High body temperature (above 39.5°C / 103°F)", "Red, hot, dry skin (no sweating, or heavy sweating in exertional cases)", "Rapid, strong pulse", "Throbbing headache", "Dizziness", "Nausea", "Confusion, delirium, or loss of consciousness"],
            "FirstAid": [
                "**Call 911 / Local Emergency immediately.**",
                "Move the person to a cooler place.",
                "Help lower the person's temperature with cool cloths, cool bath, or ice packs (armpits, groin, neck).",
                "Do NOT give the person anything to drink if they are unresponsive or confused."
            ]
        }
    }
