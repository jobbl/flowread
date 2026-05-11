import traceback
from transformers import AutoTokenizer, AutoModelForCausalLM
try:
    print("Loading Tokenizer...")
    AutoTokenizer.from_pretrained("unsloth/gemma-4-E2B")
    print("Loading Model...")
    AutoModelForCausalLM.from_pretrained("unsloth/gemma-4-E2B")
except Exception as e:
    traceback.print_exc()
