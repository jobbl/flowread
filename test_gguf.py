from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "unsloth/gemma-4-26B-A4B-it-GGUF"
gguf_file = "gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_id, gguf_file=gguf_file)
print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    gguf_file=gguf_file,
    device_map="auto"
)
print(f"Model loaded on device {model.device}, dtype: {model.dtype}")

inputs = tokenizer("Hello world", return_tensors="pt").to(model.device)
with torch.no_grad():
    out = model(**inputs, output_attentions=True)
    
print("Attentions returned:", len(out.attentions) if out.attentions else "No")
