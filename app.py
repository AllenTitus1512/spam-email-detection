from pathlib import Path

import joblib
from flask import Flask, render_template, request

from train_model import MODEL_PATH, train_model


app = Flask(__name__)


def load_model():
    if not MODEL_PATH.exists():
        train_model()
    return joblib.load(MODEL_PATH)


@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    confidence = None
    email_text = ""

    if request.method == "POST":
        email_text = request.form.get("email_text", "").strip()

        if email_text:
            model = load_model()
            predicted_label = model.predict([email_text])[0]
            probabilities = model.predict_proba([email_text])[0]
            classes = list(model.classes_)
            confidence = round(float(probabilities[classes.index(predicted_label)]) * 100, 2)
            prediction = "Phishing / Spam" if predicted_label == "phishing" else "Legitimate"

    return render_template(
        "index.html",
        prediction=prediction,
        confidence=confidence,
        email_text=email_text,
    )


if __name__ == "__main__":
    app.run(debug=True)
