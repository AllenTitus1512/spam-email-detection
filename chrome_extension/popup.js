// popup.js - handles UI interactions and backend communication

const BACKEND_URL = "http://localhost:5000/api/analyze"; // adjust if your backend runs elsewhere

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  attemptAutoFill();
  $("analyzeBtn").addEventListener("click", onAnalyze);
});

function showSpinner(show){
  const s = $("spinner");
  if(show) s.classList.remove("hidden"); else s.classList.add("hidden");
}

function showMessage(text, isError=false){
  const m = $("message");
  m.textContent = text;
  m.style.color = isError ? "#ffb4b4" : "#bfe3d4";
  m.classList.remove("hidden");
  setTimeout(()=>m.classList.add("hidden"), 5000);
}

function setResult(data){
  const res = $("result");
  const statusText = $("statusText");
  const statusIcon = $("statusIcon");
  const confidence = $("confidence");
  const risk = $("risk");
  const reason = $("reason");
  const method = $("method");

  res.classList.remove("hidden");
  statusText.textContent = data.prediction || "Unknown";
  confidence.textContent = `Confidence: ${data.confidence}%`;
  method.textContent = `Method: ${data.method || 'Unknown'}`;
  reason.textContent = data.reason || "No explanation provided.";

  // risk color + icon
  risk.textContent = `Risk: ${data.risk || 'Low'}`;
  risk.className = 'meta-item';
  if(data.risk === 'High') { risk.classList.add('risk-high'); statusIcon.textContent = '⚠️' }
  else if(data.risk === 'Medium') { risk.classList.add('risk-medium'); statusIcon.textContent = '🟡' }
  else { risk.classList.add('risk-low'); statusIcon.textContent = '🟢' }

  // status color by prediction
  if(data.prediction === 'Phishing') {
    statusText.style.color = '#ffb4b4';
  } else {
    statusText.style.color = '#bfe3d4';
  }
}

function attemptAutoFill(){
  // Ask the content script for the currently open email (works on Gmail pages)
  chrome.tabs.query({active:true,currentWindow:true}, (tabs)=>{
    if(!tabs || !tabs[0]) return;
    chrome.tabs.sendMessage(tabs[0].id, {action: 'GET_EMAIL'}, (resp) => {
      if(chrome.runtime.lastError){
        // content script not available or not on Gmail; allow manual paste
        console.log('No content script response:', chrome.runtime.lastError.message);
        return;
      }
      if(resp && resp.email){
        $("emailText").value = resp.email;
        showMessage('Email auto-filled from page', false);
      }
    });
  });
}

async function onAnalyze(){
  const email = $("emailText").value.trim();
  if(!email){ showMessage('Please paste or open an email to analyze.', true); return; }

  showSpinner(true);
  try{
    const resp = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({email_text: email})
    });

    if(!resp.ok){
      const err = await resp.json().catch(()=>({error:'Server error'}));
      showMessage(`Error: ${err.error || resp.statusText}`, true);
      showSpinner(false);
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icon.svg'),
        title: 'PhishGuard — Analysis Failed',
        message: err.error || 'Backend error'
      });
      return;
    }

    const data = await resp.json();
    // If Gemini was unavailable, backend will provide method 'Local ML Model'
    setResult(data);
    showSpinner(false);

    chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icon.svg'),
      title: `PhishGuard — ${data.prediction}`,
      message: `${data.prediction} — Confidence: ${data.confidence}% — Risk: ${data.risk}`
    });

  }catch(e){
    showSpinner(false);
    showMessage('Failed to connect to backend. Is it running?', true);
    chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icon.svg'),
      title: 'PhishGuard — Connection Error',
      message: String(e)
    });
  }
}
