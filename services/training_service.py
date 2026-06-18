import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold, GridSearchCV, train_test_split
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.inspection import permutation_importance
import joblib
import os
from datetime import datetime

def calculate_heat_index(temp_c, humidity):
    """Calculates Heat Index (Apparent Temperature) in Celsius."""
    # Convert to Fahrenheit
    T = (temp_c * 9/5) + 32
    R = humidity
    
    # Simple formula for low temperature
    if T < 80:
        HI = 0.5 * (T + 61.0 + ((T - 68.0) * 1.2) + (R * 0.094))
    else:
        # Rothfusz regression
        HI = (
            -42.379 + 2.04901523*T + 10.14333127*R - 0.22475541*T*R -
            0.00683783*T*T - 0.05481717*R*R + 0.00122874*T*T*R +
            0.00085282*T*R*R - 0.00000199*T*T*R*R
        )
        # Adjustments
        if R < 13 and 80 <= T <= 112:
            adjustment = ((13 - R) / 4) * np.sqrt((17 - np.abs(T - 95.0)) / 17)
            HI -= adjustment
        elif R > 85 and 80 <= T <= 87:
            adjustment = ((R - 85) / 10) * ((87 - T) / 5)
            HI += adjustment
            
    # Convert back to Celsius
    return round((HI - 32) * 5/9, 2)

def generate_synthetic_data(num_samples=5000, seed=42):
    np.random.seed(seed)
    
    # Generate random base features
    age = np.random.randint(5, 85, num_samples)
    body_temp = np.round(np.random.uniform(36.0, 42.5, num_samples), 1)
    water_intake = np.round(np.random.uniform(0.2, 5.0, num_samples), 1)
    dizziness = np.random.choice([0, 1], num_samples, p=[0.7, 0.3])
    headache = np.random.choice([0, 1], num_samples, p=[0.6, 0.4])
    heart_rate = np.random.randint(60, 150, num_samples)
    outdoor_temp = np.round(np.random.uniform(22.0, 46.0, num_samples), 1)
    humidity = np.round(np.random.uniform(10.0, 90.0, num_samples), 1)
    
    heat_indices = np.array([calculate_heat_index(t, h) for t, h in zip(outdoor_temp, humidity)])
    
    # Probabilities based on physiological correlations
    muscle_cramps = []
    nausea = []
    confusion = []
    
    for i in range(num_samples):
        # Muscle cramps: high heat index + low water
        if water_intake[i] < 1.5 and heat_indices[i] >= 38.0:
            cramps_p = 0.65
        else:
            cramps_p = 0.15
        muscle_cramps.append(np.random.choice([0, 1], p=[1 - cramps_p, cramps_p]))
        
        # Nausea: high body temperature / heat exhaustion
        if body_temp[i] >= 38.5:
            nausea_p = 0.55
        else:
            nausea_p = 0.12
        nausea.append(np.random.choice([0, 1], p=[1 - nausea_p, nausea_p]))
        
        # Confusion: key indicator of heatstroke (body temp >= 39.5)
        if body_temp[i] >= 40.5:
            conf_p = 0.85
        elif body_temp[i] >= 39.5:
            conf_p = 0.50
        else:
            conf_p = 0.02
        confusion.append(np.random.choice([0, 1], p=[1 - conf_p, conf_p]))
        
    muscle_cramps = np.array(muscle_cramps)
    nausea = np.array(nausea)
    confusion = np.array(confusion)
    
    risk_labels = []
    for i in range(num_samples):
        score = 0.0
        
        # Body Temperature
        if body_temp[i] >= 40.5:
            score += 7.0  # Heatstroke threshold
        elif body_temp[i] >= 39.0:
            score += 4.5  # Hyperthermia / Heat exhaustion
        elif body_temp[i] >= 38.0:
            score += 2.0  # Mild fever/overheating
            
        # Hydration (relative to environment & body temp)
        if water_intake[i] < 1.0:
            score += 3.5
        elif water_intake[i] < 2.0:
            score += 1.5
            
        # Clinical Symptoms
        if dizziness[i] == 1:
            score += 2.0
        if headache[i] == 1:
            score += 1.0
        if muscle_cramps[i] == 1:
            score += 1.5
        if nausea[i] == 1:
            score += 1.5
        if confusion[i] == 1:
            score += 5.0  # Confusion is heavily weighted towards Heatstroke
            
        # Heart Rate
        if heart_rate[i] >= 120:
            score += 2.5
        elif heart_rate[i] >= 100:
            score += 1.0
            
        # Environment Risk (Heat Index)
        if heat_indices[i] >= 41.0: # Danger zone
            score += 3.0
        elif heat_indices[i] >= 33.0: # Extreme caution
            score += 1.5
            
        # Age Vulnerability
        if age[i] >= 65 or age[i] <= 10:
            score += 1.5
            
        # Determine classification
        if score >= 8.5 or body_temp[i] >= 41.0 or (confusion[i] == 1 and body_temp[i] >= 39.5):
            risk_labels.append(2)  # High
        elif score >= 4.0:
            risk_labels.append(1)  # Medium
        else:
            risk_labels.append(0)  # Low

    df = pd.DataFrame({
        "Age": age,
        "BodyTemp": body_temp,
        "WaterIntake": water_intake,
        "Dizziness": dizziness,
        "Headache": headache,
        "HeartRate": heart_rate,
        "OutdoorTemp": outdoor_temp,
        "Humidity": humidity,
        "HeatIndex": heat_indices,
        "MuscleCramps": muscle_cramps,
        "Nausea": nausea,
        "Confusion": confusion,
        "Risk": risk_labels
    })
    return df

def train_and_save_model():
    print("Generating synthetic clinical dataset (5000 samples)...")
    df = generate_synthetic_data(5000)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    artifact_data_dir = os.path.join(current_dir, "artifacts", "data")
    artifact_model_dir = os.path.join(current_dir, "artifacts", "models")
    os.makedirs(artifact_data_dir, exist_ok=True)
    os.makedirs(artifact_model_dir, exist_ok=True)
    
    # Save the generated dataset for local reference
    df.to_csv(os.path.join(artifact_data_dir, "synthetic_heatstroke_dataset.csv"), index=False)
    
    # Features and target
    features = [
        "Age", "BodyTemp", "WaterIntake", "Dizziness", "Headache", "HeartRate", 
        "OutdoorTemp", "Humidity", "HeatIndex", "MuscleCramps", "Nausea", "Confusion"
    ]
    X = df[features]
    y = df["Risk"]
    
    # Train-test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Multi-model evaluation using Stratified 5-Fold Cross Validation
    print("Evaluating models with Stratified 5-Fold Cross Validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    candidate_models = {
        "RandomForest": (RandomForestClassifier(random_state=42), {
            "n_estimators": [50, 100],
            "max_depth": [6, 8, 10]
        }),
        "GradientBoosting": (GradientBoostingClassifier(random_state=42), {
            "n_estimators": [50, 100],
            "learning_rate": [0.05, 0.1],
            "max_depth": [3, 5]
        }),
        "SVM": (SVC(probability=True, random_state=42), {
            "C": [1, 10],
            "kernel": ["rbf"]
        })
    }
    
    best_score = 0.0
    best_model_name = ""
    
    # Evaluate models on CV
    for name, (model, _) in candidate_models.items():
        scores = []
        for train_idx, val_idx in cv.split(X_train, y_train):
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
            model.fit(X_tr, y_tr)
            preds = model.predict(X_val)
            scores.append(accuracy_score(y_val, preds))
        avg_score = np.mean(scores)
        print(f" - {name} Average CV Accuracy: {avg_score * 100:.2f}%")
        if avg_score > best_score:
            best_score = avg_score
            best_model_name = name
            
    print(f"Selected Best Model Class: {best_model_name}")
    
    # Hyperparameter search on best model
    model_obj, param_grid = candidate_models[best_model_name]
    grid_search = GridSearchCV(model_obj, param_grid, cv=cv, scoring="accuracy", n_jobs=1)
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    print(f"Best parameters: {grid_search.best_params_}")
    
    # Final evaluation on held-out test dataset
    test_preds = best_model.predict(X_test)
    accuracy = accuracy_score(y_test, test_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, test_preds, average="macro")
    conf_mtx = confusion_matrix(y_test, test_preds)
    
    print(f"Final Test Accuracy: {accuracy * 100:.2f}%")
    print(classification_report(y_test, test_preds, target_names=["Low", "Medium", "High"]))
    
    # Calculate Permutation Importance for UI charts
    print("Calculating permutation feature importances...")
    imp_result = permutation_importance(best_model, X_test, y_test, n_repeats=5, random_state=42)
    feature_importances = dict(zip(features, np.round(imp_result.importances_mean, 4)))
    
    # Save model artifact dictionary
    model_data = {
        "model": best_model,
        "model_type": best_model_name,
        "features": features,
        "feature_importances": feature_importances,
        "metrics": {
            "accuracy": round(float(accuracy) * 100, 2),
            "precision": round(float(precision) * 100, 2),
            "recall": round(float(recall) * 100, 2),
            "f1_score": round(float(f1) * 100, 2)
        },
        "confusion_matrix": conf_mtx.tolist(),
        "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Ensure save directory is local path of training script
    model_save_path = os.path.join(artifact_model_dir, "heatstroke_model.joblib")
    joblib.dump(model_data, model_save_path)
    print(f"Model successfully saved to '{model_save_path}'")

if __name__ == "__main__":
    train_and_save_model()
