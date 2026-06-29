import pandas as pd
import os
from datetime import datetime


def save_patient(
    username,
    temp,
    water,
    dizziness,
    headache,
    risk,
    bmi
):

    df = pd.DataFrame({

        "Date_Time": [
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ],

        "Username": [username],

        "Temperature": [temp],

        "Water Intake": [water],

        "Dizziness": [dizziness],

        "Headache": [headache],

        "Risk": [risk],

        "BMI": [bmi]

    })

    file_exists = os.path.exists(
        "patient_data.csv"
    )

    df.to_csv(
        "patient_data.csv",
        mode="a",
        header=not file_exists,
        index=False
    )

    print(
        "✅ Data Saved Successfully"
    )