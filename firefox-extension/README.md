# FlowRead Firefox Extension

The FlowRead Firefox extension allows you to dynamically bold the most semantically important words on any webpage, directly in your browser. It does this by communicating with your local (or cloud-hosted) FlowRead API server powered by Gemma 4 models.

## 1. Start the Backend API Server

The extension needs a running backend server to perform the mathematical saliency extraction. The backend uses the Hugging Face `transformers` library, served via FastAPI.

**Step 1: Install Dependencies**
Ensure you are in the root directory of the project and install the requirements:
```bash
pip install -r requirements.txt
```

**Step 2: Authenticate with Hugging Face**
The Gemma 4 models are gated on Hugging Face. You must log in first:
```bash
huggingface-cli login
```

**Step 3: Start the Server**
Run the backend using Uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*Note: This will download and load `unsloth/gemma-4-E2B` (or the configured 26B variant) and start listening for requests on port 8000. It does not use `llama.cpp` or `llama-server`; it uses PyTorch and the Hugging Face ecosystem natively.*

## 2. Install the Firefox Extension

1. Open Firefox and navigate to `about:debugging`.
2. Click **"This Firefox"** on the left sidebar.
3. Click the **"Load Temporary Add-on..."** button.
4. In the file dialog, navigate to the `firefox-extension` folder in this repository and select the `manifest.json` file. (Alternatively, you can select the `flowread-extension.zip` file if you prefer to use the packaged version).
5. The extension will appear in your list of Temporary Extensions and its icon will appear in your toolbar.

## 3. Configure the Extension

1. Click the **FlowRead icon** in your Firefox toolbar.
2. In the settings popup, locate the **Backend API URL** field.
3. Ensure it matches where your backend server is running:
   - If running locally: `http://127.0.0.1:8000`
   - If using Hugging Face Spaces or another remote server: `https://your-domain.com` (do not include a trailing slash)
4. You can also tweak other settings like the Saliency Threshold and Gradient Mode. Click **Save Settings**.

## 4. How to Use It

1. Navigate to any article, blog post, or text-heavy website.
2. **Method 1 (Selection):** Highlight a paragraph of text, right-click it, and select **"FlowRead Highlight"** from the context menu.
3. **Method 2 (Entire Page):** Right-click anywhere on the page and select **"FlowRead Entire Page"** (or use the "FlowRead Page" button in the extension popup).
4. The extension will send the text to your local API, compute the attention values, and instantly transform the text on your screen!