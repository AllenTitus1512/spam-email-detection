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
        print("[OK] ML Model loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load ML model: {e}")
        model = None

# Try to load Gemini API
genai = None
try:
    import google.genai as genai
except:
    pass

api_key = os.getenv("GEMINI_API_KEY")
client = None
GEMINI_MODELS = ("gemini-flash-latest", "gemini-flash-lite-latest")
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


def assess_local_phishing_risk(email_text: str) -> tuple[float, list[str]]:
    """
    Score phishing patterns that the statistical model can underweight.

    The trained model remains the main detector. This layer catches readable
    combinations such as a request verb plus sensitive personal data, or a
    brand/account notice plus a link and urgency.
    """
    if not email_text:
        return 0.0, []

    text = email_text.lower()
    reasons = []
    score = 0.0

    urls = re.findall(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+', text)
    suspicious_tlds = ('.ru', '.tk', '.xyz', '.top', '.club', '.info', '.zip', '.mov')
    shorteners = ('bit.ly', 'tinyurl', 't.co/', 'goo.gl', 'ow.ly', 'is.gd', 'cutt.ly')
    brand_terms = (
        'paypal', 'apple', 'amazon', 'microsoft', 'google', 'gmail', 'netflix',
        'linkedin', 'twitter', 'bank', 'irs', 'social security', 'dhl', 'fedex',
        'ups', 'office 365', 'outlook', 'mailbox'
    )
    action_terms = (
        'verify', 'confirm', 'validate', 'update', 'renew', 'reset', 'restore',
        'unlock', 'reactivate', 'sign in', 'sign-in', 'login', 'complete',
        'review', 'refresh'
    )
    urgency_terms = (
        'urgent', 'immediately', 'today', 'within 24 hours', 'within 48 hours',
        'last chance', 'before midnight', 'expires', 'suspended', 'locked',
        'penalty', 'warrant', 'under investigation', 'archived'
    )
    sensitive_terms = (
        'password', 'pin', 'passcode', 'credit card', 'debit card', 'bank account',
        'routing number', 'wire transfer', 'social security', 'ssn',
        "mother's maiden name", 'date of birth', 'dob', 'driver license',
        "driver's license", 'passport', 'tax id', 'business tax id',
        'employee id', 'salary information', 'current salary', 'job title',
        'home address', 'phone number', 'id documents', 'photo id',
        'billing profile', 'card on file', 'one-time code', 'username'
    )
    request_terms = (
        'send', 'reply', 'provide', 'confirm', 'verify', 'submit', 'upload',
        'share', 'enter', 'complete', 'needs', 'requires', 'refresh'
    )
    authority_terms = (
        'law enforcement', 'police', 'court', 'warrant', 'irs',
        'social security administration', 'interpol', 'nsa', 'city hall',
        'tax penalty'
    )
    money_terms = (
        'earn', 'paid', 'prize', 'reward', 'winner', 'lottery', 'inheritance',
        'per week', 'survey', '$5000', '$5,000', 'no experience needed'
    )

    has_url = bool(urls) or 'click here' in text or 'use this link' in text
    suspicious_url = any(
        any(marker in url for marker in suspicious_tlds + shorteners)
        or re.search(r'(paypal|apple|amazon|google|gmail|microsoft|netflix)[-.].+\.', url)
        for url in urls
    )
    has_brand = any(term in text for term in brand_terms)
    has_action = any(term in text for term in action_terms)
    has_urgency = any(term in text for term in urgency_terms)
    has_sensitive = any(term in text for term in sensitive_terms)
    asks_for_info = any(term in text for term in request_terms)
    has_authority = any(term in text for term in authority_terms)
    has_money_hook = any(term in text for term in money_terms)

    if has_sensitive and asks_for_info:
        score += 0.45
        reasons.append("Requests personal, identity, financial, or employee data")

    if has_brand and has_action and (has_url or has_urgency):
        score += 0.30
        reasons.append("Uses brand/account impersonation with an action request")

    if suspicious_url:
        score += 0.35
        reasons.append("Contains a suspicious or mismatched link")
    elif has_url and has_action:
        score += 0.15
        reasons.append("Pushes the user toward an external link")

    if has_authority and (has_urgency or has_action):
        score += 0.35
        reasons.append("Uses authority or legal pressure")

    if has_money_hook and (has_action or has_url or 'no experience needed' in text):
        score += 0.30
        reasons.append("Uses an unrealistic money, prize, or job offer")

    if has_urgency and has_action:
        score += 0.15
        reasons.append("Adds urgency to force quick action")

    return min(score, 1.0), reasons


def combine_phishing_scores(ml_score: float, local_risk_score: float) -> float:
    """
    Combine model and local-rule evidence without globally lowering the threshold.
    A weak ML signal plus a weak rule signal can be enough when both point in the
    same direction.
    """
    combined_evidence = ml_score + (local_risk_score * 0.5)
    return min(1.0, max(ml_score, local_risk_score, combined_evidence))


def should_flag_phishing(
    ml_score: float,
    local_risk_score: float,
    threshold: float = 0.25,
) -> bool:
    """
    Decide when to flag phishing from combined model and local-rule evidence.
    """
    return combine_phishing_scores(ml_score, local_risk_score) >= threshold

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

        response = None
        last_error = None
        for model_name in GEMINI_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                break
            except Exception as e:
                last_error = e

        if response is None:
            raise last_error or RuntimeError("No Gemini response received")
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
