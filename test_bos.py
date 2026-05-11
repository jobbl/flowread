from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("unsloth/gemma-4-E2B", extra_special_tokens={})
print("add_bos_token:", tokenizer.add_bos_token)
print("tokens:", tokenizer("hello")["input_ids"])
