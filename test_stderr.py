import sys
import re

class StderrInterceptor:
    def __init__(self, original):
        self.original = original

    def write(self, s):
        self.original.write(s)
        match = re.search(r'(\d+)%\|', s)
        if match:
            self.original.write(f"\nINTERCEPTED: {match.group(1)}%\n")
            self.original.flush()
    
    def flush(self):
        self.original.flush()

sys.stderr = StderrInterceptor(sys.stderr)

from transformers import AutoConfig
AutoConfig.from_pretrained("gpt2", force_download=True)
