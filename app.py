from pathlib import Path
import os
from dotenv import load_dotenv

# Load .env file FIRST, before any other imports
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

import joblib
from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import BadRequest

from train_model import MODEL_PATH, train_model
from gemini_detector import detect_with_gemini

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

def load_model():
    """Load the trained ML model, train if not exists"""
    if not MODEL_PATH.exists():
        print("[INFO] Training model...")
        train_model()
    return joblib.load(MODEL_PATH)

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    confidence = None
    reason = None
    email_text = ""
    error = None

    if request.method == "POST":
        try:
            email_text = request.form.get("email_text", "").strip()

            if not email_text:
                error = "ERROR: Please provide an email to analyze"
            else:
                # Try Gemini AI first (primary detector)
                gemini_label, gemini_conf, gemini_reason = detect_with_gemini(email_text)
                
                if gemini_label:
                    prediction = gemini_label
                    confidence = gemini_conf
                    reason = gemini_reason
                else:
                    # Fallback to ML model
                    try:
                        model = load_model()
                        pred_label = model.predict([email_text])[0]
                        probs = model.predict_proba([email_text])[0]
                        classes = list(model.classes_)
                        confidence = round(float(probs[classes.index(pred_label)]) * 100, 2)
                        prediction = "Phishing" if pred_label == "phishing" else "Legitimate"
                        reason = "Local ML Model (Gemini unavailable)"
                    except Exception as e:
                        error = f"❌ Error during analysis: {str(e)}"
        
        except BadRequest:
            error = "ERROR: Request too large. Please provide a shorter email."
        except Exception as e:
            error = f"ERROR: Unexpected error: {str(e)}"

    return render_template(
        "index.html",
        prediction=prediction,
        confidence=confidence,
        reason=reason,
        email_text=email_text,
        error=error,
    )

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle request too large error"""
    return render_template("index.html", error="ERROR: Request too large. Please provide a shorter email."), 413

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    return render_template("index.html", error="ERROR: Internal server error. Please try again."), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)