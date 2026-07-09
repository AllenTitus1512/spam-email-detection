"""
Debug script to analyze phishing email confidence scores
"""
import joblib
from pathlib import Path
from model import extract_email_body

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "phishing_email_model.joblib"

# Load model
model = joblib.load(str(MODEL_PATH))
print("✅ Model loaded\n")

# Common phishing email examples to test
test_emails = [
    # Real phishing patterns
    """From: security@paypal-update.com
To: user@example.com
Subject: Urgent: Verify Your Account

Dear Customer,

Your PayPal account has been locked due to suspicious activity. Please verify your account immediately by clicking the link below:

https://paypal-verify.suspicious-domain.com/login

If you don't act within 24 hours, your account will be permanently closed.

Best regards,
PayPal Security Team""",

    """Subject: Click here to claim your prize!

Congratulations! You have won $5,000 in our daily lottery. 
Click here to claim: http://bit.ly/claim-prize-now

This offer expires in 24 hours!""",

    """From: hr@company-update.net
Subject: Important: W2 Form Required

Please fill out the attached W2 tax form and submit your banking information:
Account: _______
Routing: _______
PIN: _______

Reply to this email immediately.""",

    """Your Amazon account has been suspended!

We noticed unusual activity on your account. Please update your payment information immediately:
https://amazon-secure.ru/login

Acting within 1 hour will restore your account.""",

    """Subject: Urgent: Update your password

Your Apple ID requires immediate password verification due to security concerns.
Click here: https://appleid-verify.tk/signin

Do not share this email. Apple will never ask for passwords via email.""",
]

print("=" * 70)
print("PHISHING EMAIL CONFIDENCE ANALYSIS")
print("=" * 70)

for i, email in enumerate(test_emails, 1):
    clean = extract_email_body(email)
    pred_proba = model.predict_proba([clean])[0]
    phishing_prob = pred_proba[1]
    legitimate_prob = pred_proba[0]
    
    print(f"\n📧 Email {i}:")
    print(f"   Phishing confidence:    {phishing_prob*100:.2f}%")
    print(f"   Legitimate confidence:  {legitimate_prob*100:.2f}%")
    print(f"   Detected at 0.60?:      {'✅ YES' if phishing_prob >= 0.60 else '❌ NO'}")
    print(f"   Detected at 0.50?:      {'✅ YES' if phishing_prob >= 0.50 else '❌ NO'}")
    print(f"   Detected at 0.40?:      {'✅ YES' if phishing_prob >= 0.40 else '❌ NO'}")
    print(f"   Detected at 0.30?:      {'✅ YES' if phishing_prob >= 0.30 else '❌ NO'}")
    print(f"   Email preview:          {clean[:100]}...")

print("\n" + "=" * 70)
print("RECOMMENDATION:")
print("=" * 70)
print("If most phishing emails score <0.60, lower the threshold.")
print("Adjust in app.py: if phishing_prob >= 0.50  (or 0.40)")
