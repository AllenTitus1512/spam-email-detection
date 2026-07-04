import os
from dotenv import load_dotenv

# Try to import Google GenAI SDK under common package names. Some installs
# expose the module as `google.genai` while others use `google.generativeai`.
# If neither is available we keep `genai = None` so the rest of the app can
# continue to run and fall back to the local ML model.
genai = None
try:
    import google.genai as genai
    print("✅ Imported google.genai")
except Exception:
    try:
        import google.generativeai as genai
        print("✅ Imported google.generativeai")
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
            print("✅ Gemini Client initialized successfully (Client)")
        else:
            # Some variants initialize via configure; adapt if available.
            if hasattr(genai, 'configure'):
                try:
                    genai.configure(api_key=api_key)
                    client = genai
                    print("✅ Gemini Client initialized successfully (configure)")
                except Exception as e:
                    print(f"❌ Failed to configure Gemini client: {e}")
            else:
                print("❌ GenAI module found but no known client initializer available")
    except Exception as e:
        print(f"❌ Failed to create Gemini Client: {e}")
elif not api_key:
    print("❌ No GEMINI_API_KEY found in .env")
else:
    print("❌ No GenAI package available; Gemini features will be disabled")


def detect_with_gemini(email_text: str):
    if not email_text or not email_text.strip() or client is None:
        return None, None, None

    prompt = f"""You are a cybersecurity expert. Analyze this email:

Return EXACTLY in this format:

LABEL: Phishing or Legitimate
CONFIDENCE: 85
REASON: Short explanation with key red flags

Email:
{email_text[:1800]}"""

    try:
        print("🔄 Calling Gemini API...")   # Debug line
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        text = response.text.strip()
        print("✅ Gemini Response received")

        label = None
        confidence = 75.0
        reason = "Gemini AI Analysis"

        for line in text.split('\n'):
            line = line.strip()
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
        print(f"❌ Gemini API Call Failed: {e}")   # This will now show clearly
        return None, None, None