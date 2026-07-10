import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

try:
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured in .env")

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents="Say 'Gemini API is working perfectly in 2026!' in one short sentence."
    )

    print("[OK] Gemini API is working.")
    print("Response:", response.text.strip())

except Exception as e:
    print("[ERROR]", str(e))
