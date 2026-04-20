import os
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("google/gemma-2b", token=os.environ.get("HF_TOKEN"))
p = "Hello"
t = " world" # starts with space
print("Pre:", tokenizer.convert_ids_to_tokens(tokenizer(p + "\n\n")["input_ids"]))
print("Full:", tokenizer.convert_ids_to_tokens(tokenizer(p + "\n\n" + t)["input_ids"]))
