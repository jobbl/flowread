import torch
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

model_id = "google/gemma-2b"

# Load the model and tokenizer globally.
# Use MPS if available, otherwise CPU. MPS (Metal Performance Shaders) works well on modern Macs.
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Loading {model_id} on {device}...")

try:
    hf_token = os.environ.get("HF_TOKEN")
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",
        token=hf_token
    ).to(device)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Make sure you are logged into Hugging Face and have access to the Gemma model.")
    print("Run `huggingface-cli login` in your terminal.")

class TextRequest(BaseModel):
    text: str

@app.post("/analyze")
async def analyze_text(request: TextRequest):
    text = request.text
    if not text.strip():
        return {"tokens": [], "scores": []}

    inputs = tokenizer(text, return_tensors="pt").to(device)
    
    with torch.no_grad():
        # Ensure we ask the model to output attentions explicitly
        outputs = model(**inputs, output_attentions=True)
        
    # Check if attentions are actually returned
    if not outputs.attentions:
        print("Warning: Model did not return attentions.")
        return {"words": []}
        
    # outputs.attentions is a tuple of (batch_size, num_heads, sequence_length, sequence_length)
    # Get the last layer's attention
    attentions = outputs.attentions[-1]
    
    # Average across all heads
    avg_attention = attentions[0].mean(dim=0)  # shape: (seq_len, seq_len)
    
    # Calculate importance: sum of attention each token *receives* from the sequence
    importance = avg_attention.sum(dim=0).cpu().float().numpy()
    
    if len(importance) > 1:
        # Normalize to 0-1, optionally excluding the first token (<bos>) from max/min calculation
        # as <bos> often has very high attention, skewing the rest
        min_score = importance[1:].min()
        max_score = importance[1:].max()
        
        normalized_scores = (importance - min_score) / (max_score - min_score)
        # Keep <bos> at max score
        normalized_scores[0] = 1.0
        normalized_scores = normalized_scores.clip(0, 1)
    else:
        normalized_scores = [1.0] * len(importance)
        
    input_ids = inputs["input_ids"][0].tolist()
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    
    result = []
    for i, t in enumerate(tokens):
        # Decode properly
        word = tokenizer.decode([input_ids[i]])
        # Special check for Gemma, decoding often removes spaces incorrectly or leaves tokens empty
        # Let's clean the raw token just in case
        raw_clean = t.replace('\u2581', ' ')
        
        # We will pass both decoded word and raw cleaned token to frontend to help render
        result.append({
            "token": raw_clean,
            "word": word,
            "score": float(normalized_scores[i])
        })
        
    return {"words": result}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)