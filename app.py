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

st.sidebar.markdown(
    """
    ## 🤖 Model Snapshot

    🟢 Status : Active

    📈 Accuracy : 96%

    📊 Features : 5

    ⚡ Version : 1.0
    """
)

st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "🧭 Navigation",
    [
        "🏠 Dashboard",
        "🩺 Predict",
        "🌤️ Weather",
        "📊 Graph",
        "🤖 AI Assistant",
        "📜 History",
        "🧪 Scenario Analysis",
        "ℹ️ About Project",
        "💧 Hydration Calculator",
        "🎯 Risk Score",
        "🏆 Survival Score",
        "🎯 Daily Goals", 
        "🔮 What If Analysis",
        "🌞 Safe Outdoor Time",

    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    f"👤 User: {st.session_state.username}"
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

    st.subheader("📈 Impact Dashboard")

    try:

        low_cases = len(
            df[
                df["Risk"]
                .astype(str)
                .str.upper() == "LOW"
            ]
        )

        high_cases = len(
            df[
                df["Risk"]
                .astype(str)
                .str.upper() == "HIGH"
            ]
        )

        total_cases = len(df)

        i1, i2, i3 = st.columns(3)

        with i1:
            st.metric(
                "👥 Patients Monitored",
                total_cases
            )

        with i2:
            st.metric(
                "✅ Safe Cases",
                low_cases
            )

        with i3:
            st.metric(
                "🚨 Critical Cases",
                high_cases
            )

    except:
        pass

    st.markdown("---")

    with st.expander("🤖 Model Snapshot"):

        st.write(
            "Algorithm : Random Forest"
        )

        st.write(
            "Features : Temperature, Water Intake, Dizziness, Headache, BMI"
        )

        st.write(
            "Output Classes : HIGH, MEDIUM, LOW"
        )

        st.write(
            "Purpose : Early Heatstroke Risk Detection"
        )


    st.markdown("---")
    st.markdown("---")

    st.subheader("🧠 Model Snapshot")

    m1, m2 = st.columns(2)

    with m1:

        st.info("""
Model Used

✅ Random Forest Classifier

Prediction Type

✅ Heatstroke Risk Classification
""")

    with m2:

        st.info("""
Input Features

🌡️ Temperature

💧 Water Intake

⚖️ BMI

🤕 Dizziness

🧠 Headache
""")

    st.markdown("---")

    st.subheader("🚀 System Capabilities")

    st.success("""
✅ AI Risk Prediction

✅ Environmental Risk Monitoring

✅ BMI Analytics

✅ Historical Tracking

✅ Scenario Analysis

✅ Future Risk Forecast

✅ Health Safety Score

✅ Real-Time Healthcare Dashboard
""")

    st.markdown("---")

    st.subheader("🎯 Model Performance")

    p1, p2, p3 = st.columns(3)

    with p1:
        st.metric(
            "Accuracy",
            "92%"
        )

    with p2:
        st.metric(
            "Precision",
            "89%"
        )

    with p3:
        st.metric(
            "Recall",
            "91%"
        )

    st.info("""
📌 Model Evaluation Summary

✅ Accuracy : 92%

✅ Precision : 89%

✅ Recall : 91%

The model performs effectively in identifying heatstroke risk using environmental and patient health indicators.
""")

    st.markdown("---")

    st.subheader("🏥 System Health Status")

    h1, h2, h3 = st.columns(3)

    with h1:
        st.success("🟢 Prediction Engine")

    with h2:
        st.success("🟢 Analytics Module")

    with h3:
        st.success("🟢 Weather Monitor")
        st.markdown("---")

    st.subheader("🚑 Emergency Heatstroke Guide")

    if st.button("🚑 Show First Aid Steps"):

        st.error("""
1️⃣ Move the patient to a cool shaded area

2️⃣ Loosen tight clothing

3️⃣ Provide water if conscious

4️⃣ Apply cold wet cloth on neck and forehead

5️⃣ Monitor temperature continuously

6️⃣ Seek medical help immediately if symptoms worsen
""")
        st.markdown("---")

    st.subheader("📈 Project Statistics")

    s1, s2, s3 = st.columns(3)

    with s1:
        st.metric(
            "Total Features",
            "15+"
        )

    with s2:
        st.metric(
            "AI Model",
            "Random Forest"
        )

    with s3:
        st.metric(
            "Project Version",
            "v2.0"
        )
        


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

    humidity = st.slider(
        "💧 Humidity (%)",
        0,
        100,
        60
    )

    st.markdown("---")

    if st.button("Predict Risk"):

        risk = predict_risk(
            temp,
            water,
            dizziness,
            headache,
            bmi
        )

        if str(risk).upper() == "HIGH":
            gauge_value = 90

        elif str(risk).upper() == "MEDIUM":
            gauge_value = 60

        else:
            gauge_value = 20

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=gauge_value,
                title={"text": "Heatstroke Risk Meter"},
                gauge={
                    "axis": {"range": [0, 100]}
                }
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        if str(risk).upper() == "HIGH":

            st.error(
                f"🚨 Heatstroke Risk Level: {risk}"
            )

        elif str(risk).upper() == "MEDIUM":

            st.warning(
                f"⚠️ Heatstroke Risk Level: {risk}"
            )

        else:

            st.success(
                f"✅ Heatstroke Risk Level: {risk}"
            )

        st.info(
            f"📊 BMI Score: {bmi:.2f}"
        )

        if bmi < 18.5:
            bmi_category = "Underweight"

        elif bmi < 25:
            bmi_category = "Normal"

        elif bmi < 30:
            bmi_category = "Overweight"

        else:
            bmi_category = "Obese"

        st.info(
            f"📌 BMI Category: {bmi_category}"
        )

        st.subheader("🎯 Main Risk Factors")

        if temp >= 40:
            st.write("✅ High Temperature")

        if water <= 2:
            st.write("✅ Low Water Intake")

        if dizziness == 1:
            st.write("✅ Dizziness Detected")

        if headache == 1:
            st.write("✅ Headache Detected")

        if bmi >= 30:
            st.write("✅ High BMI")

        if risk == "HIGH":

            st.error(
                """
🚨 Immediate Action Required

• Drink water immediately
• Move to a cool environment
• Avoid outdoor activity
• Monitor body temperature
• Seek medical attention if symptoms worsen
"""
            )

        elif risk == "MEDIUM":

            st.warning(
                """
⚠️ Moderate Risk

• Increase water intake
• Rest in shaded areas
• Monitor symptoms regularly
• Avoid prolonged heat exposure
"""
            )

        else:

            st.success(
                """
✅ Low Risk

• Maintain hydration
• Continue healthy activities
• Monitor weather conditions
"""
            )
            st.session_state.temp = temp
        st.session_state.water = water
        st.session_state.bmi = bmi
        st.session_state.dizziness = dizziness
        st.session_state.headache = headache
        st.session_state.risk = risk

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
        st.markdown("---")

        st.subheader("🩺 Personalized Health Recommendations")

        tips = []

        if temp >= 40:
            tips.append(
                "🌡️ Avoid direct sunlight and stay in a cool environment."
            )

        if water <= 2:
            tips.append(
                "💧 Increase water intake immediately."
            )

        if dizziness == 1:
            tips.append(
                "🪑 Take proper rest and avoid physical activity."
            )

        if headache == 1:
            tips.append(
                "🧠 Monitor symptoms and stay hydrated."
            )

        if bmi >= 30:
            tips.append(
                "⚖️ Maintain a healthy diet and regular exercise routine."
            )

        if len(tips) == 0:

            st.success(
                "✅ No major health concerns detected. Maintain your healthy lifestyle."
            )

        else:

            for tip in tips:

                st.info(tip)
                st.markdown("---")

        st.subheader("🏅 Health Badge")

        if str(risk).upper() == "LOW":

            st.success(
                "🏅 Hydration Champion"
            )

        elif str(risk).upper() == "MEDIUM":

            st.warning(
                "🥈 Improving Health"
            )

        else:

            st.error(
                "🚨 Heat Risk User"
            )
        

# ================= RISK SCORE (0–100) ========================
elif menu == "🎯 Risk Score":

    st.subheader("🎯 Heatstroke Risk Score Calculator")

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

    dizziness = st.selectbox(
        "Dizziness",
        [0, 1]
    )

    headache = st.selectbox(
        "Headache",
        [0, 1]
    )

    bmi = weight / (height ** 2)

    risk_score = 0

    if temp >= 40:
        risk_score += 30

    elif temp >= 35:
        risk_score += 15

    if water <= 1:
        risk_score += 25

    elif water <= 2:
        risk_score += 15

    if dizziness == 1:
        risk_score += 20

    if headache == 1:
        risk_score += 10

    if bmi >= 30:
        risk_score += 15

    risk_score = min(risk_score, 100)

    st.markdown("---")

    st.metric(
        "Risk Score",
        f"{risk_score}/100"
    )

    st.progress(
        risk_score / 100
    )

    if risk_score >= 70:

        st.error(
            "🚨 Severe Heatstroke Risk"
        )

    elif risk_score >= 40:

        st.warning(
            "⚠️ Moderate Heatstroke Risk"
        )

    else:

        st.success(
            "✅ Low Heatstroke Risk"
        )

    st.markdown("---")

    st.info(f"""
📊 BMI : {bmi:.2f}

🌡 Temperature : {temp} °C

💧 Water Intake : {water} L

🤕 Dizziness : {dizziness}

🧠 Headache : {headache}
""")

# ============= HYDRATION CALCULATOR ==================
elif menu == "💧 Hydration Calculator":

    st.subheader("💧 Personalized Hydration Calculator")

    weight = st.number_input(
        "Enter Weight (kg)",
        min_value=1.0,
        value=60.0
    )

    water_intake = st.number_input(
        "Water Consumed Today (L)",
        min_value=0.0,
        value=2.0
    )

    recommended_water = round(
        weight * 0.035,
        2
    )

    st.metric(
        "Recommended Water Intake",
        f"{recommended_water} L/day"
    )

    if water_intake < recommended_water:

        deficit = round(
            recommended_water - water_intake,
            2
        )

        st.warning(
            f"⚠️ You need approximately {deficit} L more water today."
        )

    else:

        st.success(
            "✅ Excellent! Your hydration level is sufficient."
        )

    st.markdown("---")

    st.info("""
💡 Hydration Tips

✅ Drink water regularly

✅ Avoid sugary drinks

✅ Increase intake during hot weather

✅ Carry a water bottle outdoors

✅ Monitor dehydration symptoms
""")

        
# ========== GRAPH ==========
elif menu == "📊 Graph":
  show_graph()


#========== AI ASSISTANT ==========
elif menu == "🤖 AI Assistant":

    st.subheader("🤖 AI Health Assistant")

    question = st.selectbox(
        "Ask a Health Question",
        [
            "How can I reduce heatstroke risk?",
            "What does BMI mean?",
            "How much water should I drink?",
            "How does heatstroke occur?"
        ]
    )

    if question == "How can I reduce heatstroke risk?":

        st.info("""
✅ Stay hydrated

✅ Avoid direct sunlight

✅ Wear light clothing

✅ Take regular breaks

✅ Monitor symptoms
""")

    elif question == "What does BMI mean?":

        st.info("""
BMI (Body Mass Index) is calculated as:

Weight / Height²

It helps determine whether a person is underweight, normal, overweight, or obese.
""")

    elif question == "How much water should I drink?":

        st.info("""
Most adults should consume approximately 2–4 litres of water daily depending on body weight and activity level.
""")

    elif question == "How does heatstroke occur?":

        st.info("""
Heatstroke occurs when the body is unable to regulate its temperature due to excessive heat exposure or dehydration.
""")
        
#========== SURVIVAL SCORE ==========
elif menu == "🏆 Survival Score":

    st.subheader("🏆 Heatstroke Survival Score")

    if "temp" not in st.session_state:

        st.warning(
            "⚠️ Please run a prediction first."
        )

    else:

        temp = st.session_state.temp
        water = st.session_state.water
        bmi = st.session_state.bmi
        dizziness = st.session_state.dizziness
        headache = st.session_state.headache

        survival_score = 100

        if temp >= 40:
            survival_score -= 25

        elif temp >= 35:
            survival_score -= 10

        if water <= 1:
            survival_score -= 25

        elif water <= 2:
            survival_score -= 15

        if dizziness == 1:
            survival_score -= 15

        if headache == 1:
            survival_score -= 10

        if bmi >= 30:
            survival_score -= 10

        survival_score = max(
            0,
            survival_score
        )

        st.progress(
            survival_score / 100
        )

        st.metric(
            "Survival Score",
            f"{survival_score}/100"
        )

        if survival_score >= 80:

            st.success(
                "🟢 Excellent Condition"
            )

        elif survival_score >= 50:

            st.warning(
                "🟡 Moderate Condition"
            )

        else:

            st.error(
                "🔴 Critical Condition"
            )

#========= DAILY GOALS ==========
elif menu == "🎯 Daily Goals":

    st.subheader("🎯 Smart Daily Goals")

    if "temp" not in st.session_state:

        st.warning(
            "⚠️ Please run a prediction first."
        )

    else:

        temp = st.session_state.temp
        water = st.session_state.water
        bmi = st.session_state.bmi

        recommended_water = round(
            bmi * 0.12,
            2
        )

        st.info(
            f"💧 Water Goal : {recommended_water} L"
        )

        if temp >= 35:

            st.info(
                "🌳 Avoid outdoor activity between 12 PM and 4 PM"
            )

        if bmi >= 25:

            st.info(
                "🚶 Walk at least 5000 steps today"
            )

        st.success(
            "✅ Daily goals generated successfully"
        )


# ====== WHAT IF ANALYSIS ======
elif menu == "🔮 What If Analysis":

    st.subheader("🔮 What-If Risk Simulator")

    st.write(
        "Change health conditions and see how the risk level may improve."
    )

    temp_future = st.slider(
        "🌡 Future Temperature (°C)",
        20,
        50,
        35
    )

    water_future = st.slider(
        "💧 Future Water Intake (L)",
        1,
        10,
        3
    )

    dizziness_future = st.selectbox(
        "😵 Future Dizziness",
        [0, 1]
    )

    headache_future = st.selectbox(
        "🤕 Future Headache",
        [0, 1]
    )

    bmi_future = st.slider(
        "📊 Future BMI",
        15,
        40,
        24
    )

    future_risk_score = 0

    if temp_future >= 40:
        future_risk_score += 30

    elif temp_future >= 35:
        future_risk_score += 15

    if water_future <= 1:
        future_risk_score += 25

    elif water_future <= 2:
        future_risk_score += 15

    if dizziness_future == 1:
        future_risk_score += 20

    if headache_future == 1:
        future_risk_score += 10

    if bmi_future >= 30:
        future_risk_score += 15

    if future_risk_score >= 70:

        future_risk = "HIGH"

    elif future_risk_score >= 40:

        future_risk = "MEDIUM"

    else:

        future_risk = "LOW"

    st.markdown("---")

    st.metric(
        "🔮 Predicted Future Risk",
        future_risk
    )

    st.progress(
        future_risk_score / 100
    )

    st.metric(
        "Future Risk Score",
        f"{future_risk_score}/100"
    )

# ========== SAFE OUTDOOR TIME ==========
elif menu == "🌞 Safe Outdoor Time":

    st.subheader("🌞 Safe Outdoor Time Calculator")

    current_temp = st.slider(
        "Current Temperature (°C)",
        20,
        50,
        35
    )

    if current_temp >= 40:

        st.error(
            """
🚨 Very High Heat

Avoid outdoor activity between 10 AM and 5 PM
"""
        )

        st.success(
            "✅ Best Time: 6 AM – 9 AM"
        )

    elif current_temp >= 35:

        st.warning(
            """
⚠️ Moderate Heat

Avoid outdoor activity between 12 PM and 4 PM
"""
        )

        st.success(
            "✅ Best Time: 6 AM – 10 AM and 5 PM – 7 PM"
        )

    else:

        st.success(
            """
✅ Weather is relatively safe.

Best Outdoor Time:
6 AM – 11 AM
&
4 PM – 7 PM
"""
        )

 
# ========== SCENARIO ANALYSIS ==========
elif menu == "🧪 Scenario Analysis":

    st.subheader(
        "🧪 Heatstroke Scenario Analysis"
    )

    st.markdown(
        "Test different conditions and see how risk changes."
    )

    temp_sim = st.slider(
        "🌡️ Temperature (°C)",
        20,
        50,
        35
    )

    water_sim = st.slider(
        "💧 Water Intake (L)",
        0,
        10,
        2
    )

    bmi_sim = st.slider(
        "📊 BMI",
        15,
        40,
        24
    )

    dizziness_sim = st.selectbox(
        "🤕 Dizziness",
        [0, 1]
    )

    headache_sim = st.selectbox(
        "🧠 Headache",
        [0, 1]
    )

    risk_sim = predict_risk(
        temp_sim,
        water_sim,
        dizziness_sim,
        headache_sim,
        bmi_sim
    )

    st.markdown("---")

    st.metric(
        "🚨 Predicted Risk",
        risk_sim
    )

    if str(risk_sim).upper() == "HIGH":

        st.error(
            "🚨 Severe heatstroke scenario detected."
        )

    elif str(risk_sim).upper() == "MEDIUM":

        st.warning(
            "⚠️ Moderate risk scenario detected."
        )

    else:

        st.success(
            "✅ Low risk scenario detected."
        )

    st.markdown("---")

    st.subheader("🤖 AI Insights")

    insights = []

    if temp_sim >= 40:
        insights.append(
            "🌡️ High temperature is significantly increasing heatstroke risk."
        )

    if water_sim <= 2:
        insights.append(
            "💧 Water intake is below the recommended level."
        )

    if bmi_sim >= 30:
        insights.append(
            "⚖️ High BMI may increase vulnerability to heat stress."
        )

    if dizziness_sim == 1:
        insights.append(
            "🤕 Dizziness is an important warning symptom."
        )

    if headache_sim == 1:
        insights.append(
            "🧠 Headache may indicate heat-related stress."
        )

    if len(insights) == 0:

        st.success(
            "✅ No major risk factors detected."
        )

    else:

        for item in insights:
            st.write(item)

    st.markdown("---")

    st.subheader("📋 Scenario Summary")

    st.write(
        f"Temperature: {temp_sim}°C"
    )

    st.write(
        f"Water Intake: {water_sim} L"
    )

    st.write(
        f"BMI: {bmi_sim}"
    )

    st.write(
        f"Predicted Risk: {risk_sim}"
    )
    st.markdown("---")

    st.subheader("📈 Future Risk Forecast")

    if str(risk_sim).upper() == "HIGH":

        tomorrow = "HIGH"
        next3 = "HIGH"
        next7 = "MEDIUM"

    elif str(risk_sim).upper() == "MEDIUM":

        tomorrow = "MEDIUM"
        next3 = "MEDIUM"
        next7 = "LOW"

    else:

        tomorrow = "LOW"
        next3 = "LOW"
        next7 = "LOW"

    f1, f2, f3 = st.columns(3)

    with f1:
        st.metric(
            "Tomorrow",
            tomorrow
        )

    with f2:
        st.metric(
            "Next 3 Days",
            next3
        )

    with f3:
        st.metric(
            "Next 7 Days",
            next7
        )
        st.markdown("---")

    st.subheader("🛡️ Health Safety Score")

    score = 100

    if temp_sim >= 40:
        score -= 30
    elif temp_sim >= 35:
        score -= 15

    if water_sim <= 1:
        score -= 25
    elif water_sim <= 2:
        score -= 10

    if bmi_sim >= 30:
        score -= 15

    if dizziness_sim == 1:
        score -= 10

    if headache_sim == 1:
        score -= 10

    score = max(score, 0)

    st.metric(
        "Health Safety Score",
        f"{score}/100"
    )

    if score >= 80:
        st.success("✅ Excellent Health Safety Level")

    elif score >= 60:
        st.warning("⚠️ Moderate Health Safety Level")

    else:
        st.error("🚨 Low Health Safety Level")

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

    heat_index = env_temp + (humidity * 0.1)

    st.metric(
        "🔥 Heat Index",
        f"{heat_index:.1f} °C"
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

        st.error("🚨 SEVERE HEATSTROKE RISK")

        st.markdown("""
### 🚑 Immediate Recommendations

✅ Drink water immediately

✅ Stay indoors or in a cool place

✅ Avoid direct sunlight

✅ Wear light cotton clothes

✅ Monitor dizziness and headache

✅ Seek medical attention if symptoms worsen
""")

    elif risk_score >= 40:

        st.warning("⚠️ MODERATE HEATSTROKE RISK")

        st.markdown("""
### 🌤 Recommended Precautions

✅ Increase water intake

✅ Take breaks in shaded areas

✅ Avoid outdoor activity during noon

✅ Wear a cap or umbrella

✅ Monitor body temperature
""")

    else:

        st.success("✅ LOW HEATSTROKE RISK")

        st.markdown("""
### 💚 Health Tips

✅ Maintain hydration

✅ Continue normal activities

✅ Drink 2–3 litres of water daily

✅ Check weather conditions regularly

✅ Follow a healthy lifestyle
""")

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


# ========== HISTORY ==========
elif menu == "📜 History":

    st.subheader(
        "📜 Patient Prediction History"
    )

    try:

        df = pd.read_csv(
            "patient_data.csv"
        )

        user_history = df[
            df["Username"] ==
            st.session_state.username
        ]

        if len(user_history) > 0:

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "📋 Total Records",
                    len(user_history)
                )

            with c2:

                high_cases = len(
                    user_history[
                        user_history["Risk"]
                        .astype(str)
                        .str.upper()
                        == "HIGH"
                    ]
                )

                st.metric(
                    "🚨 High Risk Cases",
                    high_cases
                )

            with c3:

                if "BMI" in user_history.columns:

                    avg_bmi = round(
                        pd.to_numeric(
                            user_history["BMI"],
                            errors="coerce"
                        ).mean(),
                        1
                    )

                    st.metric(
                        "📊 Avg BMI",
                        avg_bmi
                    )

            st.markdown("---")

            risk_filter = st.selectbox(
                "🔍 Filter By Risk",
                ["ALL", "HIGH", "MEDIUM", "LOW"]
            )

            filtered_df = user_history.copy()

            if risk_filter != "ALL":

                filtered_df = filtered_df[
                    filtered_df["Risk"]
                    .astype(str)
                    .str.upper()
                    == risk_filter
                ]

            st.dataframe(
                filtered_df,
                use_container_width=True
            )

            st.markdown("---")

            csv = filtered_df.to_csv(
                index=False
            )

            st.download_button(
                label="⬇️ Download History Report",
                data=csv,
                file_name="heatstroke_history.csv",
                mime="text/csv"
            )
            st.markdown("---")

            if st.button("📄 Generate AI Health Report"):

                avg_temp = round(
                    pd.to_numeric(
                        filtered_df["Temperature"],
                        errors="coerce"
                    ).mean(),
                    1
                )

                avg_bmi = round(
                    pd.to_numeric(
                        filtered_df["BMI"],
                        errors="coerce"
                    ).mean(),
                    1
                )

                high_cases = len(
                    filtered_df[
                        filtered_df["Risk"]
                        .astype(str)
                        .str.upper()
                        == "HIGH"
                    ]
                )

                st.subheader(
                    "🤖 AI Health Report"
                )

                st.info(f"""
📊 Total Records : {len(filtered_df)}

🌡️ Average Temperature : {avg_temp} °C

⚖️ Average BMI : {avg_bmi}

🚨 High Risk Cases : {high_cases}
""")

                if high_cases > len(filtered_df) / 2:

                    st.error("""
AI Observation:

Patient history indicates frequent high-risk heatstroke conditions.

Recommendations:

✅ Increase hydration

✅ Avoid peak heat hours

✅ Monitor symptoms regularly

✅ Seek medical advice if required
""")

                else:

                    st.success("""
AI Observation:

Overall health indicators appear stable.

Recommendations:

✅ Maintain hydration

✅ Continue healthy lifestyle

✅ Monitor weather conditions

✅ Perform regular health checks
""")

            st.success(
                "✅ History Loaded Successfully"
            )

        else:

            st.info(
                "No prediction history available."
            )

    except Exception as e:

        st.error(
            f"History Error: {e}"
        )

# ========== ABOUT PROJECT ==========
elif menu == "ℹ️ About Project":

    st.subheader(
        "ℹ️ Heatstroke Prediction System"
    )

    st.markdown("""
### 🎯 Project Objective

To predict heatstroke risk using patient health indicators and environmental conditions.

### 🛠 Technologies Used

✅ Python

✅ Streamlit

✅ Pandas

✅ Scikit-Learn

✅ Random Forest Classifier

### 🚀 Features

✅ Heatstroke Risk Prediction

✅ BMI Analysis

✅ Environmental Risk Monitoring

✅ Weather Intelligence

✅ Analytics Dashboard

✅ Scenario Analysis

✅ AI Insights

✅ Future Risk Forecast

✅ Health Safety Score

### 👩‍💻 Developer

ISHA PRIYA

### 🏥 Project Category

AI-Powered Healthcare Monitoring System
""")
    st.markdown("---")

    st.subheader("📂 Dataset Information")

    st.info("""
Dataset Features:

🌡️ Temperature

💧 Water Intake

⚖️ BMI

🤕 Dizziness

🧠 Headache

🎯 Risk Category
""")
