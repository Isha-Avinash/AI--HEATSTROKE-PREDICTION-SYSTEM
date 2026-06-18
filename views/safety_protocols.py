import streamlit as st

from views.ui_helpers import get_first_aid_guide


def render_safety_protocols():
    """Renders heat illness safety guidance and emergency first aid."""
    st.markdown("### Safety Protocols & Emergency First Aid")
    st.write("Review heat-stress warning signs and response steps for field teams, event staff, and supervisors.")

    guides = get_first_aid_guide()
    col_g1, col_g2 = st.columns(2)

    with col_g1:
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
        symptoms_li = "".join([f"<li>{sym}</li>" for sym in guides["Heat Stroke (Medical Emergency)"]["Symptoms"]])
        first_aid_li = "".join([f"<li>🚨 {fa}</li>" for fa in guides["Heat Stroke (Medical Emergency)"]["FirstAid"]])

        g2_html = f"""
        <div class='emergency-box'>
            <h3 style='margin-top:0; color:white;'>🔴 Heat Stroke (Critical Emergency)</h3>
            <p style='color:white;'>Heatstroke is a life-threatening emergency. The body's heat-regulating system can fail, and body temperature may spike to critical levels.</p>
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
