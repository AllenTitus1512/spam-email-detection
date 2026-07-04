from pathlib import Path
from flask import Flask, render_template, request, jsonify
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


@app.after_request
def add_cors_headers(response):
    # Allow extension requests from the Chrome extension (and for testing).
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response


@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def api_analyze():
    """Minimal JSON API for extensions/clients to analyze email text.

    This mirrors the logic used by the web form: try Gemini first,
    fallback to the local ML model. Returns JSON with keys:
    - prediction, confidence, reason, method, risk
    """
    if request.method == "OPTIONS":
        return ("", 204)

    data = request.get_json(silent=True) or {}
    email_text = (data.get("email_text") or request.form.get("email_text") or "").strip()

    if not email_text:
        return jsonify({"error": "No email_text provided"}), 400

    try:
        gemini_output = detect_with_gemini(email_text)

        if gemini_output and gemini_output[0] is not None:
            prediction, confidence, reason = gemini_output
            method = "Gemini AI"
        else:
            if ml_model:
                pred_label = ml_model.predict([email_text])[0]
                prob = max(ml_model.predict_proba([email_text])[0])
                prediction = "Phishing" if pred_label == "phishing" else "Legitimate"
                confidence = round(prob * 100, 2)
                reason = "Basic ML prediction (Gemini unavailable)"
                method = "Local ML Model"
            else:
                return jsonify({"error": "No ML model available"}), 500

        # simple risk heuristic
        risk = "Low"
        try:
            conf_val = float(confidence)
        except Exception:
            conf_val = 0.0

        if prediction == "Phishing":
            if conf_val >= 85:
                risk = "High"
            elif conf_val >= 60:
                risk = "Medium"
            else:
                risk = "Low"
        else:
            # legitimate emails typically low risk; low-confidence legitimate -> Medium
            if conf_val < 50:
                risk = "Medium"
            else:
                risk = "Low"

        resp = {
            "prediction": prediction,
            "confidence": confidence,
            "reason": reason,
            "method": method,
            "risk": risk,
        }

        return jsonify(resp)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)