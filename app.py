
from flask import Flask, render_template, request, jsonify
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

app = Flask(__name__)

# Find files relative to this app.py file
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "students.csv"

SUBJECTS = [
    "english",
    "mathematics",
    "science",
    "social_studies"
]

FEATURES = SUBJECTS + ["attendance", "study_hours"]


# -----------------------------
# Train the machine learning model
# -----------------------------
def train_model():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Cannot find students.csv at {DATASET_PATH}"
        )

    data = pd.read_csv(DATASET_PATH)

    missing = [col for col in FEATURES if col not in data.columns]

    if missing:
        raise ValueError(
            f"Missing columns in students.csv: {', '.join(missing)}"
        )

    # Convert required columns to numeric values
    for col in FEATURES:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=FEATURES)

    if len(data) < 5:
        raise ValueError(
            "students.csv must contain at least 5 valid student records."
        )

    # Ensure marks and attendance are within their expected ranges
    for subject in SUBJECTS:
        data = data[data[subject].between(0, 100)]

    data = data[data["attendance"].between(0, 100)]
    data = data[data["study_hours"].between(0, 24)]

    if len(data) < 5:
        raise ValueError(
            "Not enough valid records in students.csv to train the model."
        )

    # Calculate the average across all four subjects
    data["overall_average"] = data[SUBJECTS].mean(axis=1)

    X = data[FEATURES]
    y = data["overall_average"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=120,
        random_state=42
    )

    model.fit(X_train, y_train)

    test_predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, test_predictions)

    # R² requires at least two test records
    if len(y_test) >= 2:
        r2 = r2_score(y_test, test_predictions)
    else:
        r2 = 0.0

    return model, mae, r2


model, model_mae, model_r2 = train_model()


# -----------------------------
# Performance category
# -----------------------------
def get_category(score):
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Needs Improvement"


# -----------------------------
# Home page
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# -----------------------------
# Student performance prediction
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Invalid request. Please submit the form again."
            }), 400

        values = {}

        # Validate subject marks
        for subject in SUBJECTS:
            if subject not in data:
                return jsonify({
                    "error": f"Missing field: {subject}"
                }), 400

            try:
                score = float(data[subject])
            except (TypeError, ValueError):
                return jsonify({
                    "error": f"Enter a valid number for {subject}."
                }), 400

            if not 0 <= score <= 100:
                return jsonify({
                    "error": f"{subject.replace('_', ' ').title()} marks must be between 0 and 100."
                }), 400

            values[subject] = score

        # Validate attendance
        try:
            attendance = float(data["attendance"])
        except (KeyError, TypeError, ValueError):
            return jsonify({
                "error": "Enter valid attendance."
            }), 400

        if not 0 <= attendance <= 100:
            return jsonify({
                "error": "Attendance must be between 0 and 100."
            }), 400

        # Validate study hours
        try:
            study_hours = float(data["study_hours"])
        except (KeyError, TypeError, ValueError):
            return jsonify({
                "error": "Enter valid study hours."
            }), 400

        if not 0 <= study_hours <= 24:
            return jsonify({
                "error": "Study hours must be between 0 and 24."
            }), 400

        values["attendance"] = attendance
        values["study_hours"] = study_hours

        # Arrange inputs in the same order used for training
        input_df = pd.DataFrame(
            [values],
            columns=FEATURES
        )

        predicted_average = float(model.predict(input_df)[0])
        predicted_average = max(0.0, min(100.0, predicted_average))

        # Calculate the actual average of the marks entered
        overall_average = sum(
            values[subject] for subject in SUBJECTS
        ) / len(SUBJECTS)

        # Format subject marks for the JavaScript chart
        subject_marks = {
            subject.replace("_", " ").title(): values[subject]
            for subject in SUBJECTS
        }

        strongest_subject = max(
            subject_marks,
            key=subject_marks.get
        )

        improvement_subject = min(
            subject_marks,
            key=subject_marks.get
        )

        # Return JSON expected by static/script.js
        return jsonify({
            "overall_average": round(overall_average, 1),
            "predicted_average": round(predicted_average, 1),
            "category": get_category(predicted_average),
            "subject_marks": subject_marks,
            "strongest_subject": strongest_subject,
            "improvement_subject": improvement_subject,
            "mae": round(float(model_mae), 2),
            "r2": round(float(model_r2), 3)
        }), 200

    except Exception:
        app.logger.exception("Error while predicting student performance")

        return jsonify({
            "error": "Prediction failed. Check the PowerShell window for details."
        }), 500


# -----------------------------
# Start Flask
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
