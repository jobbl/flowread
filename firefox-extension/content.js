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
    const settings = await browser.storage.local.get(['threshold', 'gradientMode', 'preprompt', 'saliencyMode', 'modelVersion', 'apiUrl']);
    const threshold = settings.threshold !== undefined ? settings.threshold : 0.35;
    const useGradient = settings.gradientMode || false;
    const preprompt = settings.preprompt || "";
    const saliencyMode = settings.saliencyMode || "local";
    const modelVersion = settings.modelVersion || "2b";
    const apiUrl = settings.apiUrl || "http://127.0.0.1:8000";
    // Default to middle layers just like the playground
    const checkedLayers = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13];

    try {
      // Start polling status
      let isFetching = true;
      const pollStatus = async () => {
        while (isFetching) {
          try {
            const statusRes = await fetch(`${apiUrl}/status`);
            if (statusRes.ok) {
              const statusData = await statusRes.json();
              if (statusData[modelVersion] && statusData[modelVersion].startsWith("downloading")) {
                const parts = statusData[modelVersion].split(": ");
                const progress = parts.length > 1 ? parts[1] : "...";
                showToast(`Downloading Gemma 4 (${modelVersion}) ${progress}... this may take a few minutes.`, 0);
              }
            }
          } catch (e) {
            // ignore network errors for status polling
          }
          await new Promise(r => setTimeout(r, 2000));
        }
      };
      pollStatus();

      // Connect to the configured API Space
      const response = await fetch(`${apiUrl}/analyze/${modelVersion}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: selectedText, 
          preprompt: preprompt,
          saliency_mode: saliencyMode,
          layers: checkedLayers 
        })
      });
      isFetching = false;

      if (!response.ok) throw new Error('API error');
      
      const data = await response.json();
      const currentTokens = data.words || [];

      // Reconstruct the HTML
      const htmlString = generateFlowReadHTML(currentTokens, threshold, useGradient);
      
      // Replace text
      range.deleteContents();
      
      const container = document.createElement('span');
      container.className = 'flowread-container';
      container.dataset.tokens = JSON.stringify(currentTokens);
      container.dataset.preprompt = preprompt;
      container.dataset.saliencyMode = saliencyMode;
      container.dataset.modelVersion = modelVersion;
      container.dataset.originalText = selectedText;
      container.innerHTML = htmlString;
      range.insertNode(container);
      
      showToast("Done!", 1500);

    } catch (err) {
      console.error(err);
      showToast("Error: Could not reach FlowRead API", 3000);
    }
  } else if (request.action === "flowread_page") {
    await processEntirePage();
  } else if (request.action === "settings_updated") {
    await updateExisting(request.settings);
  }
});

async function processEntirePage() {
  const settings = await browser.storage.local.get(['threshold', 'gradientMode', 'preprompt', 'saliencyMode', 'modelVersion', 'apiUrl']);
  const threshold = settings.threshold !== undefined ? settings.threshold : 0.35;
  const useGradient = settings.gradientMode || false;
  const preprompt = settings.preprompt || "";
  const saliencyMode = settings.saliencyMode || "local";
  const modelVersion = settings.modelVersion || "2b";
  const apiUrl = settings.apiUrl || "http://127.0.0.1:8000";
  const checkedLayers = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13];

  // To prevent freezing the browser or overwhelming the API, process in batches
  const walkerObj = document.createTreeWalker(
    document.body,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode: function(node) {
        const text = node.nodeValue.trim();
        // Skip very short fragments
        if (text.split(/\s+/).length < 5) {
          return NodeFilter.FILTER_SKIP;
        }

        // Exclude specific parent tags
        let p = node.parentNode;
        const excludeTags = ['SCRIPT', 'STYLE', 'NOSCRIPT', 'BUTTON', 'INPUT', 'TEXTAREA', 'CODE', 'PRE', 'NAV', 'HEADER', 'FOOTER', 'A', 'SELECT', 'OPTION', 'svg'];
        
        while (p && p !== document.body) {
          if (excludeTags.includes(p.tagName)) {
            return NodeFilter.FILTER_REJECT;
          }
          if (p.classList && p.classList.contains('flowread-container')) {
             return NodeFilter.FILTER_REJECT;
          }
          p = p.parentNode;
        }
        
        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

  const nodesToProcess = [];
  let currentNode;
  while (currentNode = walkerObj.nextNode()) {
    // Exclude hidden elements dynamically
    const element = currentNode.parentElement;
    if (element) {
      const style = window.getComputedStyle(element);
      if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
         nodesToProcess.push(currentNode);
      }
    } else {
      nodesToProcess.push(currentNode);
    }
  }

  if (nodesToProcess.length === 0) {
    showToast("No suitable text found on page.", 2000);
    return;
  }

  // To prevent freezing the browser or overwhelming the API, process in batches
  const batchSize = 3;
  let processedCount = 0;

  // Polling logic for first request
  let isFetchingStatus = true;
  const pollStatus = async () => {
    while (isFetchingStatus) {
      try {
        const statusRes = await fetch(`${apiUrl}/status`);
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          if (statusData[modelVersion] && statusData[modelVersion].startsWith("downloading")) {
            const parts = statusData[modelVersion].split(": ");
            const progress = parts.length > 1 ? parts[1] : "...";
            showToast(`Downloading Gemma 4 (${modelVersion}) ${progress}... this may take a few minutes.`, 0);
          }
        }
      } catch (e) {}
      await new Promise(r => setTimeout(r, 2000));
    }
  };
  pollStatus();

  for (let i = 0; i < nodesToProcess.length; i += batchSize) {
    const batch = nodesToProcess.slice(i, i + batchSize);
    
    // Only show analyzing text if not downloading
    const statusResTemp = await fetch(`${apiUrl}/status`).catch(() => null);
    if (!statusResTemp || !statusResTemp.ok) {
       showToast(`FlowRead analyzing page (${processedCount}/${nodesToProcess.length} blocks)...`, 0);
    } else {
       const statusJson = await statusResTemp.json();
       if (!statusJson[modelVersion] || !statusJson[modelVersion].startsWith("downloading")) {
          showToast(`FlowRead analyzing page (${processedCount}/${nodesToProcess.length} blocks)...`, 0);
       }
    }

    await Promise.all(batch.map(async (node) => {
      const text = node.nodeValue;
      if (!text.trim()) return;

      try {
        const response = await fetch(`${apiUrl}/analyze/${modelVersion}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            text: text, 
            preprompt: preprompt,
            saliency_mode: saliencyMode,
            layers: checkedLayers 
          })
        });

        if (!response.ok) return;
        const data = await response.json();
        if (!data.words) return;

        const htmlString = generateFlowReadHTML(data.words, threshold, useGradient);
        
        const container = document.createElement('span');
        container.className = 'flowread-container';
        container.dataset.tokens = JSON.stringify(data.words);
        container.dataset.preprompt = preprompt;
        container.dataset.saliencyMode = saliencyMode;
        container.dataset.modelVersion = modelVersion;
        container.dataset.originalText = text;
        container.innerHTML = htmlString;
        
        if (node.parentNode) {
           node.parentNode.replaceChild(container, node);
        }

      } catch (err) {
        console.error("Batch error on node:", err);
      }
    }));
    
    processedCount += batch.length;
  }

  isFetchingStatus = false;
  showToast(`Done! Analyzed ${processedCount} blocks.`, 2000);
}

async function updateExisting(newSettings) {
  const threshold = newSettings.threshold !== undefined ? newSettings.threshold : 0.35;
  const useGradient = newSettings.gradientMode || false;
  const preprompt = newSettings.preprompt || "";
  const saliencyMode = newSettings.saliencyMode || "local";
  const modelVersion = newSettings.modelVersion || "2b";
  const apiUrl = newSettings.apiUrl || "http://127.0.0.1:8000";
  const checkedLayers = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13];

  const containers = document.querySelectorAll('.flowread-container');
  if (containers.length === 0) return;

  let reFetchCount = 0;
  let rerenderCount = 0;
  let isFetchingStatus = false;

  for (const container of containers) {
    const oldPreprompt = container.dataset.preprompt || "";
    const oldMode = container.dataset.saliencyMode || "local";
    const oldModelVersion = container.dataset.modelVersion || "2b";
    const text = container.dataset.originalText;
    if (!text) continue;

    if (oldPreprompt !== preprompt || oldMode !== saliencyMode || oldModelVersion !== modelVersion) {
      if (reFetchCount === 0) {
         showToast("Updating FlowRead elements with new settings...", 0);
         isFetchingStatus = true;
         (async () => {
           while (isFetchingStatus) {
             try {
               const statusRes = await fetch(`${apiUrl}/status`);
               if (statusRes.ok) {
                 const statusData = await statusRes.json();
                 if (statusData[modelVersion] && statusData[modelVersion].startsWith("downloading")) {
                   const parts = statusData[modelVersion].split(": ");
                   const progress = parts.length > 1 ? parts[1] : "...";
                   showToast(`Downloading Gemma 4 (${modelVersion}) ${progress}... this may take a few minutes.`, 0);
                 }
               }
             } catch (e) {}
             await new Promise(r => setTimeout(r, 2000));
           }
         })();
      }
      try {
        const response = await fetch(`${apiUrl}/analyze/${modelVersion}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            text: text, 
            preprompt: preprompt,
            saliency_mode: saliencyMode,
            layers: checkedLayers 
          })
        });

        if (!response.ok) continue;
        const data = await response.json();
        if (!data.words) continue;

        container.dataset.tokens = JSON.stringify(data.words);
        container.dataset.preprompt = preprompt;
        container.dataset.saliencyMode = saliencyMode;
        container.dataset.modelVersion = modelVersion;
        const htmlString = generateFlowReadHTML(data.words, threshold, useGradient);
        container.innerHTML = htmlString;
        reFetchCount++;
      } catch (err) {
        console.error("Update error:", err);
      }
    } else {
      // Just re-render visuals locally (super fast)
      try {
        const tokens = JSON.parse(container.dataset.tokens);
        const htmlString = generateFlowReadHTML(tokens, threshold, useGradient);
        container.innerHTML = htmlString;
        rerenderCount++;
      } catch (e) {
        console.error("Error parsing tokens", e);
      }
    }
  }

  isFetchingStatus = false;

  if (reFetchCount > 0) {
    showToast(`Updated ${reFetchCount} blocks with new AI intent!`, 2000);
  } else if (rerenderCount > 0) {
    showToast(`Updated visuals for ${rerenderCount} blocks!`, 1500);
  }
}

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
