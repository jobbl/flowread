---
title: FlowRead AI
emoji: 📖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# FlowRead AI (Gemma 4 Good Hackathon Submission)

**Accelerate reading comprehension using LLM attention vectors.**

FlowRead AI is an accessibility and educational tool that dynamically bolds the most semantically important words in a text. It uses the raw, internal attention vectors of the **Google Gemma 2B** model to understand what words actually matter, creating a visually guided reading path that reduces cognitive load and improves reading comprehension.

## The Problem
In the digital age, information overload is a massive barrier. General readers experience reduced reading speeds and poor retention when trying to skim long articles or academic papers, and individuals with ADHD, dyslexia, or cognitive fatigue face even more significant challenges when processing dense blocks of text. Existing solutions (like "Bionic Reading") simply bold the first half of *every* word, which is arbitrary and ignores the actual meaning of the sentence. 

## The Solution
FlowRead AI solves this by extracting the mathematical "saliency" of words. By averaging the incoming attention scores across different layers of Gemma 2B, we determine exactly which nouns, verbs, and adjectives anchor the semantic meaning of the sentence. 

For the general reader, this translates to significantly faster reading speeds and highly efficient skimming, as the eye is naturally drawn to the most information-dense words. For readers with attention deficits or cognitive fatigue, it creates a visually guided reading path that reduces cognitive load and improves reading comprehension. Everyone benefits from a more focused reading experience.

**Key Features:**
* **True Semantic Saliency:** Real mathematical LLM attention extraction, ensuring only truly important words are emphasized.
* **Intent-Driven Reading:** By preprompting Gemma (e.g., *"Focus on numbers and dates"*), the internal attention mechanism dynamically shifts, allowing the user to read texts through specific "lenses."
* **Optimal Layer Selection:** Users can explore how Gemma thinks by peeking into the middle layers (semantic understanding) vs. the last layer (next-token prediction).
* **Built-in A/B User Study:** A complete embedded research tool with an SQLite backend to gather real-world empirical data on how FlowRead impacts average reading speed and comprehension accuracy.

## Why Gemma?
We chose **Gemma 2B** because it offers an incredible balance of deep semantic understanding and computational efficiency. At just 2 billion parameters, its attention heads are remarkably accurate at capturing contextual importance, punching well above its weight class. Because it has open weights, we can directly extract the `outputs.attentions` matrices—something impossible with closed-source, API-based models. Its compact size means the entire application can run locally on consumer hardware (like Macs with MPS) or on free cloud tiers (like Hugging Face Spaces), democratizing access to this tool.

## Technical Implementation
* **Backend:** FastAPI (Python) serving a PyTorch/Hugging Face pipeline.
* **Model:** `google/gemma-2b` running in `bfloat16` precision.
* **Frontend:** Pure HTML/JS/CSS with a minimalist, distraction-free "academic paper" aesthetic.
* **Database:** SQLite for storing A/B test results.

## How to Deploy and Run

FlowRead AI can be run locally on your machine or deployed directly to Hugging Face Spaces.

### Option 1: Run Locally (Recommended for Development)

Running locally allows you to use your own GPU (like Apple Silicon MPS or Nvidia CUDA) for significantly faster processing.

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Authenticate with Hugging Face:**
   Gemma 2B is a gated model. You must accept the terms on Hugging Face and log in:
   ```bash
   huggingface-cli login
   ```
3. **Start the Server:**
   You can start the FastAPI server using Uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
4. **Open the Web App:**
   Navigate to `http://localhost:8000` in your browser.

### Option 2: Deploy to Hugging Face Spaces (Docker)

This repository is already configured with a `Dockerfile` and the correct YAML frontmatter to be deployed directly as a Hugging Face Docker Space.

1. Create a new **Docker Space** on Hugging Face.
2. Add your Hugging Face Token as a Repository Secret named `HF_TOKEN`. This is required to download the gated Gemma 2B model.
3. Push this repository to your Space.
4. The Space will automatically build the Docker image and start the FastAPI server. The SQLite database (`study.db`) is safely written to the `/tmp` or `/data` directory to avoid read-only filesystem errors.

## FlowRead Firefox Extension

You can use FlowRead directly on any website using the included Firefox Extension! The extension communicates with your FlowRead backend (either Local or Hugging Face) to highlight text directly on the page.

### How to Install the Extension:
1. Locate the `flowread-extension.zip` file in this repository (or the `firefox-extension` folder).
2. Open Firefox and navigate to `about:debugging`.
3. Click **"This Firefox"** on the left sidebar.
4. Click **"Load Temporary Add-on..."**.
5. Select the `manifest.json` file inside the `firefox-extension` folder (or select the `.zip` file).

### How to Configure and Use:
1. **Set your Backend URL:** Click the FlowRead icon in your Firefox toolbar. In the settings popup, set the **Backend API URL**:
   - If running locally: Enter `http://127.0.0.1:8000`
   - If using Hugging Face: Enter your Space URL (e.g., `https://your-username-flowread.hf.space`)
2. **Read:** Highlight any paragraph of text on any website.
3. **FlowRead It:** Right-click the highlighted text and select **"FlowRead Highlight"**.
4. The text on the page will dynamically transform using Gemma's attention vectors!

## The User Study (Help Us Prove It Works!)
The web application includes a built-in **3-Minute Study**. The system randomly assigns users to read plain text, FlowRead (bolding), or FlowRead (gradient) text. It times their reading speed, tests their comprehension, and asks for their preference. The global statistics dashboard proves the real-world impact of Gemma-powered saliency!
