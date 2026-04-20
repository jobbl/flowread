document.addEventListener('DOMContentLoaded', () => {
  const thresholdInput = document.getElementById('threshold');
  const thresholdVal = document.getElementById('threshold-val');
  const gradientModeInput = document.getElementById('gradient-mode');
  const prepromptInput = document.getElementById('preprompt');
  const apiUrlInput = document.getElementById('api-url');
  const saveBtn = document.getElementById('save-btn');
  const pageBtn = document.getElementById('page-btn');

  // Load existing settings
  browser.storage.local.get(['threshold', 'gradientMode', 'preprompt', 'apiUrl'], (res) => {
    if (res.threshold !== undefined) {
      thresholdInput.value = res.threshold;
      thresholdVal.textContent = parseFloat(res.threshold).toFixed(2);
    }
    if (res.gradientMode !== undefined) {
      gradientModeInput.checked = res.gradientMode;
    }
    if (res.preprompt !== undefined) {
      prepromptInput.value = res.preprompt;
    }
    apiUrlInput.value = res.apiUrl || "http://127.0.0.1:8000";
  });

  // Update threshold label
  thresholdInput.addEventListener('input', (e) => {
    thresholdVal.textContent = parseFloat(e.target.value).toFixed(2);
  });

  // Save settings
  saveBtn.addEventListener('click', () => {
    const settings = {
      threshold: parseFloat(thresholdInput.value),
      gradientMode: gradientModeInput.checked,
      preprompt: prepromptInput.value.trim(),
      apiUrl: apiUrlInput.value.trim().replace(/\/$/, '') // Remove trailing slash
    };
    
    browser.storage.local.set(settings).then(() => {
      saveBtn.textContent = 'Saved!';
      setTimeout(() => saveBtn.textContent = 'Save Settings', 1500);

      // Notify the active tab to automatically recompute text
      browser.tabs.query({active: true, currentWindow: true}, (tabs) => {
        if (tabs[0]) {
          browser.tabs.sendMessage(tabs[0].id, { action: "settings_updated", settings: settings });
        }
      });
    });
  });

  pageBtn.addEventListener('click', () => {
    browser.tabs.query({active: true, currentWindow: true}, (tabs) => {
      if (tabs[0]) {
        browser.tabs.sendMessage(tabs[0].id, { action: "flowread_page" });
        window.close(); // Close popup
      }
    });
  });
});
