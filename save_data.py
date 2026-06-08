import pandas as pd
import os

def save_patient(temp, water, dizziness, headache, risk, bmi):
    df = pd.DataFrame({
        "Temperature":[temp],
        "Water Intake":[water],
        "Dizziness":[dizziness],
        "Headache":[headache],
        "Risk":[risk],
        "BMI":[bmi]
    })

    df.to_csv(
        "patient_data.csv",
        mode="a",
        header=not
          os.path.exists("patient_data.csv"),
        index=False
    )

    print("Data Saved Successfully!")