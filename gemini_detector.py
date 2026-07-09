import os
from dotenv import load_dotenv

# Try to import Google GenAI SDK under common package names. Some installs
# expose the module as `google.genai` while others use `google.generativeai`.
# If neither is available we keep `genai = None` so the rest of the app can
# continue to run and fall back to the local ML model.
genai = None
try:
    import google.genai as genai
    print("[OK] Imported google.genai")
except Exception:
    try:
        import google.generativeai as genai
        print("[OK] Imported google.generativeai")
    except Exception:
        genai = None
        # Will not raise here; application will fallback to local model when Gemini is unavailable.

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = None

if api_key and genai is not None:
    try:
        # Prefer a Client constructor if present (google.genai style).
        if hasattr(genai, 'Client'):
            client = genai.Client(api_key=api_key)
            print("[OK] Gemini Client initialized successfully (Client)")
        else:
            # Some variants initialize via configure; adapt if available.
            if hasattr(genai, 'configure'):
                try:
                    genai.configure(api_key=api_key)
                    client = genai
                    print("[OK] Gemini Client initialized successfully (configure)")
                except Exception as e:
                    print(f"[ERROR] Failed to configure Gemini client: {e}")
            else:
                print("[ERROR] GenAI module found but no known client initializer available")
    except Exception as e:
        print(f"[ERROR] Failed to create Gemini Client: {e}")
elif not api_key:
    print("[ERROR] No GEMINI_API_KEY found in .env")
else:
    print("[ERROR] No GenAI package available; Gemini features will be disabled")


def detect_with_gemini(email_text: str):
    if not email_text or not email_text.strip() or client is None:
        return None, None, None

    prompt = f"""You are a cybersecurity expert. Analyze this email and determine if it's phishing or legitimate.

Return EXACTLY in this format:

LABEL: Phishing or Legitimate
CONFIDENCE: 85
REASON: Detailed explanation with specific red flags (for phishing) or why it's safe (for legitimate)

Email:
{email_text[:2000]}"""

    try:
        print("[INFO] Calling Gemini API...")
        
        # Try the new google.genai API first
        if hasattr(client, 'models') and hasattr(client.models, 'generate_content'):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
        # Fall back to old google.generativeai API
        elif hasattr(genai, 'GenerativeModel'):
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
        else:
            return None, None, None
        
        text = response.text.strip()
        print("[OK] Gemini Response received")

        label = None
        confidence = 75.0
        reason = "Gemini AI Analysis"

        # Parse response - handle multi-line reason
        lines = text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
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
                # Capture everything after REASON: including multi-line reasons
                reason_text = line.split(":", 1)[1].strip()
                # Collect remaining lines until we hit another field or end
                i += 1
                while i < len(lines) and not lines[i].strip().upper().startswith(("LABEL:", "CONFIDENCE:", "REASON:")):
                    next_line = lines[i].strip()
                    if next_line:
                        reason_text += " " + next_line
                    i += 1
                reason = reason_text if reason_text else "Gemini AI Analysis"
                i -= 1  # Adjust since we'll increment at the end of loop
            i += 1

        return label, round(confidence, 1), reason

    except Exception as e:
        print(f"[ERROR] Gemini API Call Failed: {e}")
        return None, None, None
