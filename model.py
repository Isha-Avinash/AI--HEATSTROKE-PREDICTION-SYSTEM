import pandas as pd
from sklearn.ensemble import RandomForestClassifier

data = pd.DataFrame({
    "Temperature": [45, 40, 38, 42, 36, 41],
    "Water": [1, 2, 3, 1, 4, 2],
    "Dizziness": [1, 1, 0, 1, 0, 1],
    "Headache": [1, 0, 0, 1, 0, 1],
    "Risk": [1, 1, 0, 1, 0, 0]
})

X = data[["Temperature", "Water", "Dizziness", "Headache"]]
y = data["Risk"]

model = RandomForestClassifier()
model.fit(X, y)

def predict_risk(temp, water, dizziness, headache):
    pred = model.predict([[temp, water, dizziness, headache]])

    return "HIGH" if pred[0] == 1 else "LOW"