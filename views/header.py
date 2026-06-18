import streamlit as st


def render_app_header():
    """Renders the client-demo app heading and safety note."""
    st.markdown("<h1 class='app-title'>Heat Stress Risk Screening Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='screening-note'>
            This demo is a decision-support screening aid, not a medical device, diagnosis system, or replacement for trained responders. If someone has confusion, collapse, loss of consciousness, or very high body temperature, start cooling and seek emergency medical care immediately.
        </div>
        """,
        unsafe_allow_html=True,
    )
