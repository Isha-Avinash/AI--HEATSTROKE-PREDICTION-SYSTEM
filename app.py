import streamlit as st
import pandas as pd

from model import predict_risk
from save_data import save_patient
from graph import show_graph
from weather import get_weather
from voice_alert import speak
from auth import login_user

st.set_page_config(page_title="Heatstroke AI System", layout="centered")
st.sidebar.title("⚙️ Settings")
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_user(username, password):
            st.session_state.login = True
            st.success("Login Successful")
        else:
            st.error("Invalid Credentials")

    st.stop()

# ================= MAIN APP =================
st.title("🔥 Heatstroke Prediction System (AI)")

menu = st.sidebar.selectbox("Menu", ["Predict", "Graph", "Weather"])

# ========== PREDICT ==========
if menu == "Predict":

    temp = st.number_input("Temperature")
    water = st.number_input("Water Intake")
    dizziness = st.selectbox("Dizziness", [0, 1])
    headache = st.selectbox("Headache", [0, 1])

    weight = st.number_input("Weight (kg)")
    height = st.number_input("Height (m)")

    bmi = weight / (height**2) if height > 0 else 0

    if st.button("Predict Risk"):
        risk = predict_risk(temp, water, dizziness, headache)

        st.success(f"Heatstroke Risk: {risk}")
        st.info(f"BMI: {bmi:.2f}")

        save_patient(temp, water, dizziness, headache, risk, bmi)

        speak(f"Risk is {risk}")
        

# ========== GRAPH ==========
elif menu == "Graph":
    st.subheader("📊 Patient Graph")
    show_graph()

# ========== WEATHER ==========
elif menu == "Weather":

    st.subheader("🌍 Live Weather Update")

    city = st.text_input("Enter City Name", "Delhi")

    if city:
        weather = get_weather(city)

        st.write(f"📍 Showing weather for: {city}")
        st.success(weather)