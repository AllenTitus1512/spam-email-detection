import os
from dotenv import load_dotenv
import google.genai as genai   # New official package

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = None

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        print("✅ Gemini (google-genai) configured successfully")
    except Exception as e:
        print(f"❌ Gemini Config Error: {e}")
else:
    print("❌ GEMINI_API_KEY not found in .env file")


def detect_with_gemini(email_text: str):
    """Detect phishing using Gemini AI"""
    if not email_text or not email_text.strip() or client is None:
        return None, None, None

    prompt = f"""You are a professional cybersecurity analyst. 
Analyze the following email and determine if it is phishing/scam or legitimate.

Return your response in **exactly** this format:

LABEL: Phishing or Legitimate
CONFIDENCE: 85
REASON: Short explanation mentioning key red flags (urgency, suspicious links, spoofing, etc.)

Email Content:
{email_text[:2000]}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        text = response.text.strip()

        label = None
        confidence = 75.0
        reason = "Gemini AI Analysis"

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.upper().startswith("LABEL:"):
                label_text = line.split(":", 1)[1].strip()
                label = "Phishing" if "phish" in label_text.lower() else "Legitimate"

            elif line.upper().startswith("CONFIDENCE:"):
                try:
                    conf_str = line.split(":", 1)[1].strip()
                    confidence = float(''.join(c for c in conf_str if c.isdigit() or c == '.'))
                except:
                    pass

            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        return label, round(confidence, 1), reason

    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return None, None, None