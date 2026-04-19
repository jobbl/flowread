# FlowRead AI (Gemma 4 Good Hackathon Submission)

**Accelerate reading comprehension using LLM attention vectors.**

FlowRead AI is an accessibility and educational tool that dynamically bolds the most semantically important words in a text. It uses the raw, internal attention vectors of the **Google Gemma 2B** model to understand what words actually matter, creating a visually guided reading path that reduces cognitive load and improves reading comprehension.

## The Problem
In the digital age, information overload is a massive barrier. For individuals with ADHD, dyslexia, or cognitive fatigue, reading dense blocks of text is exhausting and hinders learning. Existing solutions (like "Bionic Reading") simply bold the first half of *every* word, which is arbitrary and ignores the actual meaning of the sentence. 

## The Solution
FlowRead AI solves this by extracting the mathematical "saliency" of words. By averaging the incoming attention scores across the middle layers of Gemma 2B, we determine exactly which nouns, verbs, and adjectives anchor the semantic meaning of the sentence. 

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

## How to Run Locally

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
   ```bash
   python main.py
   ```
4. **Open the Web App:**
   Navigate to `http://localhost:7860/static/index.html` in your browser.

## The User Study (Help Us Prove It Works!)
When you deploy this project to Hugging Face Spaces, users can take the built-in **2-Minute Study**. The system randomly assigns users to read plain text vs. FlowRead text, times their reading speed, and tests their comprehension. The global statistics dashboard proves the real-world impact of Gemma-powered saliency!