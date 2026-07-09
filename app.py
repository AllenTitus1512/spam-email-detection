from pathlib import Path
from flask import Flask, render_template, request, jsonify
import joblib

from gemini_detector import detect_with_gemini
from model import extract_email_body, extract_phishing_indicators

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
        # Extract only the body, removing headers and metadata
        clean_email = extract_email_body(email_text)
        email_preview = clean_email[:300] + "..." if len(clean_email) > 300 else clean_email

        if clean_email:
            # === PRIORITY: Use ML Model FIRST (fast & accurate on 63K emails) ===
            if ml_model:
                pred_proba = ml_model.predict_proba([clean_email])[0]
                phishing_prob = pred_proba[1]
                
                # Use 0.25 threshold - catches 92.1% of phishing including sophisticated patterns
                if phishing_prob >= 0.25:
                    prediction = "Phishing"
                    confidence = round(phishing_prob * 100, 2)
                    reason = extract_phishing_indicators(clean_email)
                    
                    # === ONLY IF PHISHING: Try Gemini for detailed reasoning ===
                    gemini_output = detect_with_gemini(clean_email)
                    if gemini_output and gemini_output[0] is not None:
                        _, gemini_conf, gemini_reason = gemini_output
                        # Use Gemini's reasoning if available
                        reason = gemini_reason if gemini_reason else reason
                        method = "🟠 ML Model + Gemini AI"
                    else:
                        method = "🔵 Local ML Model (Trained on 63K emails)"
                else:
                    # === Legitimate: Skip Gemini entirely ===
                    prediction = "Legitimate"
                    confidence = round((1 - phishing_prob) * 100, 2)
                    reason = "Email passes phishing checks"
                    method = "🟢 Local ML Model (No Gemini needed)"

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

    # Extract only the body, removing headers and metadata
    clean_email = extract_email_body(email_text)

    try:
        # === PRIORITY: Use ML Model FIRST (fast & accurate) ===
        if ml_model:
            pred_proba = ml_model.predict_proba([clean_email])[0]
            phishing_prob = pred_proba[1]
            
            # Use 0.25 threshold - catches 92.1% of phishing including sophisticated patterns
            if phishing_prob >= 0.25:
                prediction = "Phishing"
                confidence = round(phishing_prob * 100, 2)
                reason = extract_phishing_indicators(clean_email)
                
                # === ONLY IF PHISHING: Try Gemini for detailed reasoning ===
                gemini_output = detect_with_gemini(clean_email)
                if gemini_output and gemini_output[0] is not None:
                    _, gemini_conf, gemini_reason = gemini_output
                    reason = gemini_reason if gemini_reason else reason
                    method = "ML Model + Gemini AI"
                else:
                    method = "Local ML Model"
            else:
                # === Legitimate: Skip Gemini entirely ===
                prediction = "Legitimate"
                confidence = round((1 - phishing_prob) * 100, 2)
                reason = "Email passes phishing checks"
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