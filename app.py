from pathlib import Path
from flask import Flask, render_template, request
import joblib

from gemini_detector import detect_with_gemini

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "phishing_email_model.joblib"

# Load ML model
ml_model = None
if MODEL_PATH.exists():
    ml_model = joblib.load(MODEL_PATH)
    print("✅ ML Model loaded successfully")
else:
    print("⚠️ ML Model not found. Please run train_model.py first.")

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    confidence = None
    reason = None
    email_preview = ""
    method = "Local ML Model"

    if request.method == "POST":
        email_text = request.form.get("email_text", "").strip()
        email_preview = email_text[:300] + "..." if len(email_text) > 300 else email_text

        if email_text:
            # === PRIORITY: Try Gemini First ===
            gemini_output = detect_with_gemini(email_text)
            
            if gemini_output and gemini_output[0] is not None:
                prediction, confidence, reason = gemini_output
                method = "🟢 Gemini AI"
            else:
                # Fallback
                if ml_model:
                    pred_label = ml_model.predict([email_text])[0]
                    prob = max(ml_model.predict_proba([email_text])[0])
                    prediction = "Phishing" if pred_label == "phishing" else "Legitimate"
                    confidence = round(prob * 100, 2)
                    reason = "Basic ML prediction (Gemini unavailable)"
                else:
                    prediction = "Error"
                    reason = "No model available"

    return render_template("index.html",
                           prediction=prediction,
                           confidence=confidence,
                           reason=reason,
                           email=email_preview,
                           method=method)

if __name__ == "__main__":
    app.run(debug=True)