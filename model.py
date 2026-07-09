import joblib
import os
from pathlib import Path
from dotenv import load_dotenv
import re

load_dotenv()

# Load local ML model with fallback
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "phishing_email_model.joblib"

model = None
if MODEL_PATH.exists():
    try:
        model = joblib.load(str(MODEL_PATH))
        print("✅ ML Model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load ML model: {e}")
        model = None

# Try to load Gemini API
genai = None
try:
    import google.genai as genai
except:
    pass

api_key = os.getenv("GEMINI_API_KEY")
client = None
if genai and api_key:
    try:
        if hasattr(genai, 'Client'):
            client = genai.Client(api_key=api_key)
    except:
        pass


def extract_email_body(email_text: str) -> str:
    """
    Extract ONLY the main email body content, aggressively removing all headers,
    metadata, timestamps, sender info, quoted replies, forwarded sections, and signatures.
    """
    if not email_text:
        return email_text
    
    text = email_text
    
    # === STEP 1: Remove ALL email headers (from/to/date/subject/etc) ===
    # Stop at first blank line (header-body separator)
    header_end = text.find('\n\n')
    if header_end != -1:
        text = text[header_end + 2:]  # Skip past the double newline
    
    # === STEP 2: Remove quoted replies ===
    # Pattern: "On [date], [person] wrote:" or "Date: ..., Sender wrote:"
    text = re.sub(r'On\s+.+?wrote:\s*\n', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Date:.+?wrote:\s*\n', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # === STEP 3: Remove forwarded email sections ===
    # "---------- Forwarded message ---------" and everything after
    text = re.sub(r'---+\s*Forwarded message\s*---+.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'------+.{0,20}begin forwarded.{0,20}------+.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # === STEP 4: Remove email signatures ===
    # Signatures typically start with "--" or "___" or after newlines with specific patterns
    text = re.sub(r'\n--\s*\n.*', '', text, flags=re.DOTALL)  # "-- " separator
    text = re.sub(r'\n_{5,}.*', '', text, flags=re.DOTALL)     # "___" separator
    text = re.sub(r'\nSent from.*', '', text, flags=re.IGNORECASE)  # "Sent from" signature
    text = re.sub(r'\nBest regards,.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\n(Sincerely|Thanks|Regards),.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # === STEP 5: Remove any remaining metadata markers ===
    # Remove ">" quoted lines (common in email threads)
    lines = text.split('\n')
    lines = [line for line in lines if not line.strip().startswith('>')]
    text = '\n'.join(lines)
    
    # === STEP 6: Clean up extra whitespace ===
    text = re.sub(r'\n\n+', '\n', text)  # Multiple newlines -> single newline
    
    return text.strip()


def extract_phishing_indicators(email_text: str) -> str:
    """
    Extract and explain potential phishing indicators in an email.
    Returns a formatted reason string.
    """
    indicators = []
    text_lower = email_text.lower()
    
    # Urgency indicators
    if any(word in text_lower for word in ['urgent', 'immediately', 'act now', 'verify now', 'confirm identity', 
                                             'verify account', 'validate', 'update information', 'click here']):
        indicators.append("Contains urgency language")
    
    # Suspicious requests
    if any(word in text_lower for word in ['password', 'credit card', 'social security', 'bank account', 
                                             'routing number', 'wire transfer', 'verify credentials']):
        indicators.append("Requests sensitive information")
    
    # Authority impersonation
    if any(word in text_lower for word in ['bank', 'paypal', 'apple', 'amazon', 'microsoft', 'google', 
                                             'irs', 'security team', 'account services', 'compliance team']):
        indicators.append("Impersonates known organization")
    
    # Suspicious URLs/Offers
    if any(word in text_lower for word in ['http://', 'prize', 'claim', 'reward', 'million', 'inheritance',
                                             'click link', 'confirm link']):
        indicators.append("Contains suspicious links or offers")
    
    # Generic greeting
    if any(word in text_lower for word in ['dear user', 'dear customer', 'dear valued', 'to whom']):
        indicators.append("Uses generic greeting (not personalized)")
    
    if not indicators:
        return "No major phishing indicators detected"
    
    return "Red flags: " + "; ".join(indicators)

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
