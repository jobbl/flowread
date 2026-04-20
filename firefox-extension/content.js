if (typeof browser === "undefined") {
  var browser = chrome;
}

// Ensure the toast element exists
function ensureToast() {
  let toast = document.getElementById('flowread-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'flowread-toast';
    document.body.appendChild(toast);
  }
  return toast;
}

function showToast(message, duration = 3000) {
  const toast = ensureToast();
  toast.textContent = message;
  toast.classList.add('show');
  if (duration > 0) {
    setTimeout(() => {
      toast.classList.remove('show');
    }, duration);
  }
}

browser.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
  if (request.action === "flowread_selection") {
    const selectedText = window.getSelection().toString();
    if (!selectedText.trim()) return;

    showToast("Analyzing text with FlowRead AI...", 0);

    // Save the selection range so we can replace it later
    const selection = window.getSelection();
    if (selection.rangeCount === 0) return;
    const range = selection.getRangeAt(0);

    // Get user settings
    const settings = await browser.storage.local.get(['threshold', 'gradientMode', 'preprompt', 'apiUrl']);
    const threshold = settings.threshold !== undefined ? settings.threshold : 0.35;
    const useGradient = settings.gradientMode || false;
    const preprompt = settings.preprompt || "";
    const apiUrl = settings.apiUrl || "http://127.0.0.1:8000";
    // Default to middle layers just like the playground
    const checkedLayers = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13];

    try {
      // Connect to the configured API Space
      const response = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: selectedText, 
          preprompt: preprompt, 
          layers: checkedLayers 
        })
      });

      if (!response.ok) throw new Error('API error');
      
      const data = await response.json();
      const currentTokens = data.words || [];

      // Reconstruct the HTML
      const htmlString = generateFlowReadHTML(currentTokens, threshold, useGradient);
      
      // Replace text
      range.deleteContents();
      
      const container = document.createElement('span');
      container.className = 'flowread-container';
      container.innerHTML = htmlString;
      range.insertNode(container);
      
      showToast("Done!", 1500);

    } catch (err) {
      console.error(err);
      showToast("Error: Could not reach FlowRead API", 3000);
    }
  }
});

// Grouping logic extracted from your frontend code
function generateFlowReadHTML(currentTokens, threshold, useGradient) {
  let html = "";
  
  let words = [];
  let currentWordTokens = [];
  let currentWordMaxScore = 0;

  currentTokens.forEach((item, index) => {
      if (index === 0 && (item.token.includes('<bos>') || item.word.includes('<bos>'))) return;

      const isWhitespace = item.token.trim() === '';
      const prevIsWhitespace = currentWordTokens.length > 0 && currentWordTokens[currentWordTokens.length - 1].token.trim() === '';

      if (item.token.startsWith(' ') || (currentWordTokens.length > 0 && isWhitespace !== prevIsWhitespace)) {
          if (currentWordTokens.length > 0) {
              words.push({ tokens: currentWordTokens, maxScore: currentWordMaxScore });
          }
          currentWordTokens = [item];
          currentWordMaxScore = item.score;
      } else {
          currentWordTokens.push(item);
          currentWordMaxScore = Math.max(currentWordMaxScore, item.score);
      }
  });
  if (currentWordTokens.length > 0) {
      words.push({ tokens: currentWordTokens, maxScore: currentWordMaxScore });
  }

  // Render words
  words.forEach(wordObj => {
      const isWordHighlighted = wordObj.maxScore >= threshold;

      wordObj.tokens.forEach(item => {
          let styleAttr = '';
          let classNames = 'flowread-token';
          
          if (useGradient) {
              const opacity = 0.4 + (item.score * 0.6);
              const weight = 400 + Math.round(item.score * 400);
              styleAttr = `opacity: ${opacity}; font-weight: ${weight}; color: inherit;`;
          } else {
              if (isWordHighlighted) {
                  classNames += ' flowread-highlighted';
              }
          }
          
          const safeText = String(item.token || "").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
          
          html += `<span class="${classNames}" ${styleAttr ? `style="${styleAttr}"` : ''}>${safeText}</span>`;
      });
  });
  
  return html;
}
