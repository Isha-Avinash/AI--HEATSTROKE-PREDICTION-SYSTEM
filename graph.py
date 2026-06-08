import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def show_graph():
    data = pd.read_csv("patient_data.csv")

    data["Temperature"] = pd.to_numeric(data["Temperature"], errors="coerce")
    data = data.dropna(subset=["Temperature"])

    fig, ax = plt.subplots()
    ax.plot(data["Temperature"], marker='o')

    ax.set_title("Temperature Graph")
    ax.set_xlabel("Patients")
    ax.set_ylabel("Temperature")

    st.pyplot(fig)