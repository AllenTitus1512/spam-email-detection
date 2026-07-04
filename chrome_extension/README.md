PhishGuard Chrome Extension
==========================

Quick instructions to load the extension and how it integrates with your existing Flask backend.

Files
- [manifest.json](chrome_extension/manifest.json)
- [popup.html](chrome_extension/popup.html)
- [popup.css](chrome_extension/popup.css)
- [popup.js](chrome_extension/popup.js)
- [content.js](chrome_extension/content.js)
- [background.js](chrome_extension/background.js)
- [icon.svg](chrome_extension/icon.svg)

How it works
- The extension's popup allows you to analyze email text.
- `content.js` runs on Gmail pages and attempts to extract the open email body.
- The popup sends the email text to the backend at `http://localhost:5000/api/analyze`.
- The backend returns JSON containing `prediction`, `confidence`, `reason`, `method`, and `risk`.

Backend note
- To allow a clean JSON integration, I added a minimal API endpoint to your Flask app: [app.py](app.py).
  - Route: `/api/analyze` (POST JSON: `{ "email_text": "..." }`)
  - The endpoint re-uses the same Gemini + ML fallback logic already present in your app.
  - CORS headers are added so the extension can call the API.

Load the extension (developer mode)
1. Start your Flask backend (usually `python app.py` or via your existing run method).
2. In Chrome, go to `chrome://extensions` and enable "Developer mode".
3. Click "Load unpacked" and select the `chrome_extension` folder inside this repository.
4. Open Gmail, open an email, then click the PhishGuard extension icon. The popup will try to auto-fill the email text.

Configuration
- If your backend runs on a different host/port, edit `popup.js` and change `BACKEND_URL`.

Security & privacy
- The extension only sends the email text to the backend you run locally at the configured `BACKEND_URL`.
- No telemetry or external servers are contacted by the extension itself.
