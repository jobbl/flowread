from transformers import AutoTokenizer
import numpy as np

tokenizer = AutoTokenizer.from_pretrained("unsloth/gemma-4-E2B", extra_special_tokens={})
preprompt = "imagine"
text = "Japan's railways are the finest in the world.\xa0"

full_text = f"{preprompt}\n\n{text}" if preprompt else text
inputs = tokenizer(full_text, return_tensors="pt")

num_preprompt_tokens = 0
if preprompt:
    p_toks = tokenizer(f"{preprompt}\n\n")["input_ids"]
    num_preprompt_tokens = len(p_toks)
elif tokenizer.bos_token_id is not None and len(inputs["input_ids"][0]) > 0 and inputs["input_ids"][0][0] == tokenizer.bos_token_id:
    num_preprompt_tokens = 1

input_ids = inputs["input_ids"][0].tolist()
tokens = tokenizer.convert_ids_to_tokens(input_ids)
has_bos = (input_ids[0] == tokenizer.bos_token_id) if len(input_ids) > 0 else False

normalized_scores = np.ones(len(tokens))

result = []
for i, t in enumerate(tokens):
    word = tokenizer.decode([input_ids[i]])
    if t.startswith('<0x') and t.endswith('>'):
        word = ""
        t = ""
    raw_clean = t.replace('\u2581', ' ')
    result.append({"token": raw_clean, "word": word})

if num_preprompt_tokens > 0 and len(result) > num_preprompt_tokens:
    if has_bos:
        result = [result[0]] + result[num_preprompt_tokens:]
    else:
        result = result[num_preprompt_tokens:]

print([r["token"] for r in result])
