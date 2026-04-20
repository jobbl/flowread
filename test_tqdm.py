import huggingface_hub.utils as hf_utils

original_tqdm = hf_utils.tqdm

class MyTqdm(original_tqdm):
    def update(self, n=1):
        super().update(n)
        if hasattr(self, 'total') and self.total:
            print(f"DL_PROGRESS: {self.n / self.total:.2%}", flush=True)

hf_utils.tqdm = MyTqdm
hf_utils.tqdm.tqdm = MyTqdm # Also overwrite the module attribute just in case

import huggingface_hub.file_download
huggingface_hub.file_download.tqdm = MyTqdm

try:
    from transformers import AutoConfig
    AutoConfig.from_pretrained("gpt2", force_download=True)
except Exception as e:
    print(e)
