import joblib
import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# Load local fallback
model = joblib.load('model/phishing_email_model.joblib')

def predict_phishing_gemini(email_text):
    """Primary: Use Gemini AI for smart detection"""
    prompt = f"""
    Analyze this email and determine if it is a **Phishing / Scam** or **Legitimate** email.
    Return output in this exact format:
    LABEL: Phishing or Legitimate
    CONFIDENCE: X% (number only)
    REASON: Short explanation with key red flags.

    Email:
    {email_text[:1500]}
    """

    try:
        if client is None:
            raise RuntimeError("Gemini API key not configured")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()

        # Parse response
        label = "Legitimate"
        confidence = 85.0
        reason = "AI Analysis"

        for line in text.split('\n'):
            line = line.strip()
            if line.upper().startswith("LABEL:"):
                label_text = line.split(":", 1)[1].strip()
                label = "Phishing" if "phish" in label_text.lower() else "Legitimate"
            elif line.upper().startswith("CONFIDENCE:"):
                try:
                    confidence = float(''.join(c for c in line.split(":", 1)[1].strip() if c.isdigit() or c == '.'))
                except Exception:
                    pass
            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        return label, round(confidence, 2), reason

    except Exception as e:
        print("Gemini Error:", e)
        # Fallback to local model
        pred = model.predict([email_text])[0]
        prob = max(model.predict_proba([email_text])[0])
        result = pred.capitalize() if isinstance(pred, str) else ("Phishing" if pred == 1 else "Legitimate")
        return result, round(prob * 100, 2), "Local ML Model (Gemini fallback)"
