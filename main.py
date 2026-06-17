import pandas as pd
import matplotlib.pyplot as plt
import pyttsx3
import requests
import os

# ---------------- MODEL (simple inline logic) ----------------
def predict_risk(temp, water, dizziness, headache):
    if temp >= 42 and water <= 2:
        return "High"
    elif temp >= 38:
        return "Medium"
    else:
        return "Low"

# ---------------- BMI ----------------
def calculate_bmi(weight, height):
    return round(weight / (height ** 2), 2)

# ---------------- VOICE ALERT ----------------
def speak_alert(risk):
    engine = pyttsx3.init()

    if risk == "High":
        msg = "Warning! High heatstroke risk detected."
    elif risk == "Medium":
        msg = "Moderate heatstroke risk. Stay hydrated."
    else:
        msg = "Low risk. You are safe."

    engine.say(msg)
    engine.runAndWait()

# ---------------- WEATHER ----------------
def get_weather(city="Delhi"):
    try:
        url = f"https://wttr.in/{city}?format=3"
        response = requests.get(url)
        print("\n🌦️ Weather:", response.text)
    except:
        print("Weather not available")

# ---------------- SAVE DATA ----------------
def save_result(temp, water, dizziness, headache, risk, bmi):

    data = {
        "Temperature": [temp],
        "Water Intake": [water],
        "Dizziness": [dizziness],
        "Headache": [headache],
        "Risk": [risk],
        "BMI": [bmi]
    }

    df = pd.DataFrame(data)

    df.to_csv(
        "patient_data.csv",
        mode="a",
        header=not os.path.exists("patient_data.csv"),
        index=False
    )

    print("Data Saved Successfully!")

# ---------------- GRAPH ----------------
def show_graph():

    data = pd.read_csv("patient_data.csv")

    data["Temperature"] = pd.to_numeric(data["Temperature"], errors="coerce")

    data.dropna(subset=["Temperature"], inplace=True)

    data["Temperature"].plot(kind="line")

    plt.title("Temperature Graph")
    plt.xlabel("Patients")
    plt.ylabel("Temperature")
    plt.show()

# ---------------- MAIN PROGRAM ----------------
print("===== HEATSTROKE PREDICTION SYSTEM =====")

temp = float(input("Enter Temperature: "))
water = float(input("Enter Water Intake: "))

dizziness = int(input("Dizziness (1=yes,0=no): "))
headache = int(input("Headache (1=yes,0=no): "))

# Prediction
risk = predict_risk(temp, water, dizziness, headache)
print("\nHeatstroke Risk:", risk)

# Voice alert
speak_alert(risk)

# Weather
city = input("\nEnter city: ")
get_weather(city)

# BMI
weight = float(input("\nEnter weight (kg): "))
height = float(input("Enter height (m): "))

bmi = calculate_bmi(weight, height)
print("Your BMI:", bmi)

# Save
save_result(temp, water, dizziness, headache, risk, bmi)

# Graph
show_graph()