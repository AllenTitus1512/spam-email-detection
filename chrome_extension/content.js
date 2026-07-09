// content.js
// Runs on Gmail pages (matches in manifest). Tries to extract the currently opened
// email body and responds to popup requests.

function extractEmailBody(){
  try{
    // Gmail email body commonly uses class 'a3s' for the message container.
    const a3s = document.querySelector('div.a3s');
    if(a3s && a3s.innerText && a3s.innerText.trim().length>20){
      return a3s.innerText.trim();
    }

    // Fallback selectors for different layouts
    const selectors = [
      'div.if',
      'div.ii',
      'article',
      'div.readable'
    ];
    for(const sel of selectors){
      const el = document.querySelector(sel);
      if(el && el.innerText && el.innerText.trim().length>20) return el.innerText.trim();
    }

    return null;
  }catch(e){
    return null;
  }
}

// Respond to popup queries
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if(msg && msg.action === 'GET_EMAIL'){
    const body = extractEmailBody();
    sendResponse({ email: body });
    return true; // indicate async (not strictly needed here)
  }
});

// Optionally detect changes and store the latest email in chrome.storage for quick access
const observer = new MutationObserver(() => {
  const body = extractEmailBody();
  if(body){
    try {
      chrome.storage.local.set({phishguard_last_email: body});
    } catch(e) {
      // Extension context may be invalidated; silently fail
      console.log('Storage unavailable (extension context invalidated)');
    }
  }
});

// Start observing body for changes (lightweight)
observer.observe(document.body, {childList:true, subtree:true});
