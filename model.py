import joblib
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load local fallback
model = joblib.load('model/phishing_model.joblib')
vectorizer = joblib.load('model/tfidf_vectorizer.joblib')

def predict_phishing_gemini(email_text):
    """Primary: Use Gemini AI for smart detection"""
    prompt = f"""
    Analyze this email and determine if it is a **Phishing / Scam** or **Legitimate** email.
    Return output in this exact format:
    LABEL: Phishing or Legitimate
    CONFIDENCE: X% (number only)
    REASON: Short explanation with key red flags.

    Email:
    {email_text[:1500]}  # Limit for API
    """

    try:
        model_gemini = genai.GenerativeModel('gemini-1.5-flash')  # Free & fast
        response = model_gemini.generate_content(prompt)
        text = response.text.strip()

        # Parse response
        lines = text.split('\n')
        label = "Phishing" if "Phishing" in text else "Legitimate"
        confidence = 85  # Default, parse if possible
        reason = "AI Analysis"

        for line in lines:
            if "CONFIDENCE" in line:
                try:
                    confidence = float(line.split(':')[1].strip().replace('%',''))
                except:
                    pass
            if "REASON" in line:
                reason = line.split(':', 1)[1].strip()

        return label, round(confidence, 2), reason

    except Exception as e:
        print("Gemini Error:", e)
        # Fallback to local model
        text_vec = vectorizer.transform([email_text])
        pred = model.predict(text_vec)[0]
        prob = model.predict_proba(text_vec)[0].max()
        result = "Phishing" if pred == 1 else "Legitimate"
        return result, round(prob * 100, 2), "Local ML Model (Gemini fallback)"