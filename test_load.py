from transformers import AutoTokenizer, AutoModelForCausalLM
try:
    hf_model_id = "unsloth/gemma-4-E2B"
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained(hf_model_id)
except Exception as e:
    import traceback
    traceback.print_exc()
