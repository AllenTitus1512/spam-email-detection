import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    # Updated model name
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    response = model.generate_content("Say 'Gemini API is working perfectly in 2026!' in one short sentence.")
    
    print("✅ SUCCESS! Gemini API is working.")
    print("Response:", response.text.strip())
    
except Exception as e:
    print("❌ Error:", str(e))