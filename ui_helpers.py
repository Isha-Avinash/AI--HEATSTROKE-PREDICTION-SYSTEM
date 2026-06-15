import streamlit as st
import streamlit.components.v1 as components

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
