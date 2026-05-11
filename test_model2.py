from transformers import AutoTokenizer
try:
    print("Loading Tokenizer with empty dict override...")
    AutoTokenizer.from_pretrained("unsloth/gemma-4-E2B", extra_special_tokens={})
    print("Loaded!")
except Exception as e:
    import traceback
    traceback.print_exc()
