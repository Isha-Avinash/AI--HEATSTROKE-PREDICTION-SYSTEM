import streamlit as st
import pandas as pd

from model import predict_risk
from save_data import save_patient
from graph import show_graph
from weather import get_weather
from voice_alert import speak
from auth import login_user, register_user
import plotly.graph_objects as go

st.set_page_config(
    page_title="Heatstroke AI Dashboard",
    page_icon="🔥",
    layout="wide"
)
st.markdown("""
<style>

/* Main Background */
.stApp{
    background-color:#0F172A;
}

/* Sidebar */
section[data-testid="stSidebar"]{
    background:linear-gradient(
        180deg,
        #111827,
        #1E293B
    );
}

/* Metric Cards */
[data-testid="stMetric"]{
    background:linear-gradient(
        135deg,
        #2563EB,
        #1D4ED8
    );
    padding:18px;
    border-radius:18px;
    border:none;
    box-shadow:0px 4px 15px rgba(0,0,0,0.3);
}

/* Buttons */
.stButton > button{
    width:100%;
    height:3em;
    border-radius:12px;
    font-weight:bold;
    border:none;
    background:linear-gradient(
        135deg,
        #2563EB,
        #3B82F6
    );
    color:white;
}

/* Inputs */
.stTextInput input,
.stNumberInput input{
    border-radius:10px;
}

/* Select Boxes */
.stSelectbox{
    border-radius:10px;
}

/* Login/Register Cards */
.login-card{
    padding:20px;
    border-radius:18px;
    background:linear-gradient(
        135deg,
        #1E293B,
        #334155
    );
    box-shadow:0px 4px 15px rgba(0,0,0,0.3);
    text-align:center;
    color:white;
}

/* Dashboard Banner */
.dashboard-banner{
    padding:20px;
    border-radius:18px;
    background:linear-gradient(
        135deg,
        #2563EB,
        #1D4ED8
    );
    color:white;
    text-align:center;
    font-size:22px;
    font-weight:bold;
    margin-bottom:15px;
}

/* Footer */
.footer{
    text-align:center;
    color:#94A3B8;
    margin-top:20px;
}

</style>
""", unsafe_allow_html=True)
st.sidebar.title("⚙️ Settings")
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])

#================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    st.markdown("""
    <div style="
    padding:35px;
    border-radius:25px;
    background:linear-gradient(135deg,#0F172A,#1E3A8A,#2563EB);
    color:white;
    text-align:center;
    box-shadow:0px 10px 30px rgba(0,0,0,0.4);
    ">

    <h1>🏥 Heatstroke AI Healthcare Portal</h1>

    <h4>Smart Heatstroke Detection & Monitoring System</h4>

    <p>
    AI Powered Risk Assessment • BMI Analysis • Weather Monitoring
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(
        ["🔐 Login", "📝 Register"]
    )

    with tab1:

        st.markdown("""
        ### 🔐 Secure Login

        Access your healthcare dashboard
        """)

        username = st.text_input(
            "👤 Username"
        )

        password = st.text_input(
            "🔑 Password",
            type="password"
        )

        if st.button("🚀 Login"):

            if login_user(
                username,
                password
            ):

                st.session_state.login = True

                st.session_state.username = username

                st.success(
                    "✅ Login Successful"
                )

                st.rerun()

            else:

                st.error(
                    "❌ Invalid Credentials"
                )

    with tab2:

        st.markdown("""
        ### 📝 Create Account

        Join the AI Healthcare Platform
        """)

        new_user = st.text_input(
            "👤 Create Username"
        )

        new_pass = st.text_input(
            "🔑 Create Password",
            type="password"
        )

        if st.button("📝 Register"):

            register_user(
                new_user,
                new_pass
            )

            st.success(
                "✅ Registration Successful! Please Login."
            )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "🤖 AI",
            "Enabled"
        )

    with col2:
        st.metric(
            "🌤️ Weather",
            "Live"
        )

    with col3:
        st.metric(
            "📊 Analytics",
            "Ready"
        )

    st.info(
        "💡 Monitor heatstroke risk using AI-powered healthcare analytics."
    )

    st.markdown("---")

    st.caption(
        "🏥 Heatstroke AI Dashboard v1.0 | Healthcare Monitoring Platform"
    )

    st.stop()

# ================= MAIN APP =================
st.markdown("""
<div style="
padding:30px;
border-radius:25px;
background:linear-gradient(135deg,#0F172A,#1E3A8A,#2563EB);
color:white;
text-align:center;
box-shadow:0px 10px 30px rgba(0,0,0,0.4);
margin-bottom:20px;
">

<h1>🏥 Heatstroke AI Healthcare Dashboard</h1>

<h4>
AI Powered Monitoring • Risk Prediction • Weather Intelligence
</h4>

<p>
Smart Healthcare Analytics & Real-Time Heatstroke Assessment
</p>

</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "🧭 Navigation",
    [
        "🏠 Dashboard",
        "🩺 Predict",
        "🌤️ Weather",
        "📊 Graph",
        "📜 History"
    ]
)

st.sidebar.markdown("---")

if st.sidebar.button("🚪 Logout"):

    st.success(
        "✅ Logged Out Successfully"
    )

    st.session_state.login = False

    st.rerun()
if menu == "🏠 Dashboard":

    st.subheader(
        f"👋 Welcome, {st.session_state.username}"
    )

    st.markdown("""
### 🏥 Healthcare System Overview

✔️ AI Risk Prediction
✔️ Live Weather Monitoring
✔️ BMI Analysis
✔️ Prediction History
✔️ Voice Alert System
✔️ Real-Time Healthcare Analytics
""")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    try:

        df = pd.read_csv("patient_data.csv")

        last = df.iloc[-1]

        with col1:
            st.metric(
                "🌡️ Temperature",
                f"{last['Temperature']} °C"
            )

        with col2:
            st.metric(
                "💧 Water Intake",
                f"{last['Water Intake']} L"
            )

        with col3:
            st.metric(
                "📊 BMI",
                round(float(last['BMI']), 2)
            )

        with col4:
            st.metric(
                "🚨 Risk",
                str(last['Risk'])
            )

    except:

        with col1:
            st.metric("🌡️ Temperature", "--")

        with col2:
            st.metric("💧 Water Intake", "--")

        with col3:
            st.metric("📊 BMI", "--")

        with col4:
            st.metric("🚨 Risk", "--")


    st.markdown("---")

    try:

        df = pd.read_csv(
            "patient_data.csv"
        )

        a1, a2, a3 = st.columns(3)

        with a1:
            st.metric(
                "📋 Total Predictions",
                len(df)
            )

        with a2:
            st.metric(
                "🚨 High Risk Cases",
                len(
                    df[
                        df["Risk"]
                        .astype(str)
                        .str.upper() == "HIGH"
                    ]
                )
            )

        with a3:
            st.metric(
                "📊 Average BMI",
                round(
                    df["BMI"].mean(),
                    1
                )
            )

    except:
        pass

    st.markdown("---")

    try:

        weather = get_weather("Delhi")

        st.success(
            f"🌤 Live Weather : {weather}"
        )

    except:
        pass

    st.markdown("---")

    st.info(
        "Monitor patients, analyze heatstroke risk, track BMI and review environmental conditions in real time using AI-powered healthcare analytics."
    )

    st.markdown("---")

    st.subheader("⚡ Quick Actions")

    q1, q2, q3 = st.columns(3)

    with q1:
        st.button("🩺 New Prediction")

    with q2:
        st.button("📊 View Analytics")

    with q3:
        st.button("🌤 Check Weather")

    st.markdown("---")

    st.caption(
        "🏥 Heatstroke AI Dashboard v1.0 | Healthcare Monitoring Platform"
    )

# ========== PREDICT ==========
elif menu == "🩺 Predict":
 
    st.subheader("🩺 Heatstroke Risk Assessment")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🌤️ Environmental Conditions")

        temp = st.number_input(
            "Temperature (°C)",
            min_value=0.0,
            max_value=60.0,
            value=35.0
        )

        water = st.number_input(
            "Water Intake (L)",
            min_value=0.0,
            max_value=20.0,
            value=2.0
        )

    with col2:

        st.markdown("### 👤 Patient Details")

        weight = st.number_input(
            "Weight (kg)",
            min_value=1.0,
            value=60.0
        )

        height = st.number_input(
            "Height (m)",
            min_value=0.1,
            value=1.60
        )

    bmi = weight / (height ** 2) if height > 0 else 0

    st.markdown("---")

    st.markdown("### 🤒 Symptoms")

    c1, c2 = st.columns(2)

    with c1:
        dizziness = st.selectbox("Dizziness", [0, 1])

    with c2:
        headache = st.selectbox("Headache", [0, 1])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🌡️ Temperature", f"{temp} °C")

    with col2:
        st.metric("💧 Water", f"{water} L")

    with col3:
        st.metric("📊 BMI", f"{bmi:.2f}")

    st.markdown("---")

    if st.button("Predict Risk"):

     risk = predict_risk(
        temp,
        water,
        dizziness,
        headache
    )

    # Risk Meter Value
    if str(risk).upper() == "HIGH":
        gauge_value = 90

    elif str(risk).upper() == "MEDIUM":
        gauge_value = 60

    else:
        gauge_value = 20

    # Gauge Meter
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=gauge_value,
            title={
                "text": "Heatstroke Risk Meter"
            },
            gauge={
                "axis": {
                    "range": [0, 100]
                }
            }
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # Risk Result
    if str(risk).upper() == "HIGH":

        st.error(
            f"🚨 Heatstroke Risk Level: {risk}"
        )

    else:

        st.success(
            f"✅ Heatstroke Risk Level: {risk}"
        )

    st.info(
        f"📊 BMI Score: {bmi:.2f}"
    )

    st.warning(
        "💧 Stay hydrated and avoid prolonged exposure to extreme heat."
    )

    save_patient(
        st.session_state.username,
        temp,
        water,
        dizziness,
        headache,
        risk,
        bmi
    )

    speak(
        f"Risk is {risk}"
    )
        
# ========== GRAPH ==========
elif menu == "📊 Graph":
    show_graph()

# ========== WEATHER ==========
elif menu == "🌤️ Weather":

    st.subheader(
        "🌤️ Environmental Risk Intelligence Center"
    )

    st.markdown("""
    Monitor environmental conditions associated with heatstroke and heat-related illnesses.
    """)

    c1, c2, c3 = st.columns(3)

    with c1:
        env_temp = st.number_input(
            "🌡️ Temperature (°C)",
            min_value=0.0,
            max_value=60.0,
            value=35.0
        )

    with c2:
        humidity = st.slider(
            "💧 Humidity (%)",
            0,
            100,
            60
        )

    with c3:
        uv = st.slider(
            "☀️ UV Index",
            0,
            15,
            6
        )

    st.markdown("---")

    risk_score = 0

    if env_temp >= 40:
        risk_score += 40
    elif env_temp >= 35:
        risk_score += 25

    if humidity >= 80:
        risk_score += 30
    elif humidity >= 60:
        risk_score += 15

    if uv >= 10:
        risk_score += 30
    elif uv >= 6:
        risk_score += 15

    if risk_score >= 70:

        st.error(
            "🚨 SEVERE HEATSTROKE RISK"
        )

    elif risk_score >= 40:

        st.warning(
            "⚠️ MODERATE HEATSTROKE RISK"
        )

    else:

        st.success(
            "✅ LOW HEATSTROKE RISK"
        )

    st.markdown("---")

    m1, m2, m3 = st.columns(3)

    with m1:
        st.metric(
            "🌡️ Temperature",
            f"{env_temp}°C"
        )

    with m2:
        st.metric(
            "💧 Humidity",
            f"{humidity}%"
        )

    with m3:
        st.metric(
            "☀️ UV Index",
            uv
        )

    st.markdown("---")

    st.info(
        "💧 Drink water regularly, avoid direct sunlight during peak hours and monitor symptoms such as dizziness, headache and fatigue."
    )

# ========== History ==========
elif menu == "📜 History":

    st.subheader("📜 My Prediction History")

    try:

        df = pd.read_csv("patient_data.csv")
        st.write(df.columns)
        st.write(df.head())

        user_history = df[
            df["Username"] == st.session_state.username
        ]

        if len(user_history) > 0:

            st.dataframe(
    user_history,
    use_container_width=True
)

            csv = user_history.to_csv(index=False)

            st.download_button(
                label="⬇️ Download My History",
                data=csv,
                file_name="my_history.csv",
                mime="text/csv"
            )

        else:

            st.info("No history available.")

    except Exception:

        st.error("History file not found.")
       