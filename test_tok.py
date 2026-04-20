import os
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b", token=os.environ.get("HF_TOKEN"))
preprompt = "Focus on numbers"
text = "The 86 billion neurons."
full = f"{preprompt}\n\n{text}"

p_tok = tokenizer(preprompt + "\n\n")["input_ids"]
f_tok = tokenizer(full)["input_ids"]
print(f"Preprompt tokens: {len(p_tok)}")
print(f"Full tokens: {len(f_tok)}")
print("Preprompt tokens:", tokenizer.convert_ids_to_tokens(p_tok))
print("Full tokens:", tokenizer.convert_ids_to_tokens(f_tok))
