import torch
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import uvicorn
import os
import sqlite3
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# --- SQLite Database Setup ---
DB_FILE = "study.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS study_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            text_id INTEGER,
            condition TEXT, -- "plain" or "flowread"
            reading_time_ms INTEGER,
            score INTEGER,
            total_questions INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Study Content ---
STUDY_TEXTS = [
    {
        "id": 1,
        "topic": "Science",
        "text": "The human brain is a marvel of biological engineering, containing approximately 86 billion neurons interconnected by trillions of synapses. These neural networks are responsible for everything from basic autonomic functions, like breathing and heart rate, to complex cognitive processes such as memory, emotion, and problem-solving. Neuroplasticity, the brain's ability to reorganize itself by forming new neural connections throughout life, allows humans to learn new skills, recover from injuries, and adapt to changing environments. This extraordinary adaptability is what makes our species so resilient and capable of continuous intellectual growth.",
        "flowread_html": '<span class="token">The</span><span class="token"> human</span><span class="token highlighted"> brain</span><span class="token"> is</span><span class="token"> a</span><span class="token"> marvel</span><span class="token"> of</span><span class="token"> biological</span><span class="token"> engineering</span><span class="token">,</span><span class="token"> containing</span><span class="token"> approximately</span><span class="token"> </span><span class="token">8</span><span class="token">6</span><span class="token"> billion</span><span class="token highlighted"> neurons</span><span class="token"> interconnected</span><span class="token"> by</span><span class="token"> tri</span><span class="token">lli</span><span class="token">ons</span><span class="token"> of</span><span class="token"> synapses</span><span class="token highlighted">.</span><span class="token"> These</span><span class="token"> neural</span><span class="token"> networks</span><span class="token"> are</span><span class="token"> responsible</span><span class="token"> for</span><span class="token"> everything</span><span class="token"> from</span><span class="token"> basic</span><span class="token"> autonomic</span><span class="token"> functions</span><span class="token">,</span><span class="token"> like</span><span class="token"> breathing</span><span class="token"> and</span><span class="token"> heart</span><span class="token"> rate</span><span class="token">,</span><span class="token"> to</span><span class="token"> complex</span><span class="token"> cognitive</span><span class="token"> processes</span><span class="token"> such</span><span class="token"> as</span><span class="token"> memory</span><span class="token">,</span><span class="token"> emotion</span><span class="token">,</span><span class="token"> and</span><span class="token"> problem</span><span class="token">-</span><span class="token">solving</span><span class="token highlighted">.</span><span class="token"> Neurop</span><span class="token highlighted">lastic</span><span class="token highlighted">ity</span><span class="token">,</span><span class="token"> the</span><span class="token"> brain</span><span class="token">\'</span><span class="token">s</span><span class="token"> ability</span><span class="token"> to</span><span class="token"> reorgan</span><span class="token">ize</span><span class="token"> itself</span><span class="token"> by</span><span class="token"> forming</span><span class="token"> new</span><span class="token"> neural</span><span class="token"> connections</span><span class="token"> throughout</span><span class="token"> life</span><span class="token">,</span><span class="token"> allows</span><span class="token"> humans</span><span class="token"> to</span><span class="token"> learn</span><span class="token"> new</span><span class="token"> skills</span><span class="token">,</span><span class="token"> recover</span><span class="token"> from</span><span class="token"> injuries</span><span class="token">,</span><span class="token"> and</span><span class="token"> adapt</span><span class="token"> to</span><span class="token"> changing</span><span class="token"> environments</span><span class="token">.</span><span class="token"> This</span><span class="token"> extraordinary</span><span class="token"> adaptability</span><span class="token"> is</span><span class="token"> what</span><span class="token"> makes</span><span class="token"> our</span><span class="token"> species</span><span class="token"> so</span><span class="token"> resilient</span><span class="token"> and</span><span class="token"> capable</span><span class="token"> of</span><span class="token"> continuous</span><span class="token"> intellectual</span><span class="token"> growth</span><span class="token">.</span>',
        "questions": [
            {
                "question": "Approximately how many neurons are in the human brain?",
                "options": ["86 million", "86 billion", "100 trillion", "50 billion"],
                "correct": 1
            },
            {
                "question": "What is the term for the brain's ability to reorganize itself?",
                "options": ["Synaptic generation", "Neurogenesis", "Neuroplasticity", "Cognitive adaptation"],
                "correct": 2
            }
        ]
    },
    {
        "id": 2,
        "topic": "History",
        "text": "The Industrial Revolution, which began in Britain in the late 18th century, marked a profound turning point in human history. It initiated the transition from agrarian, handicraft economies to industry and machine manufacturing. The invention of the steam engine, pioneered by figures like James Watt, dramatically increased the efficiency of factories and transportation, revolutionizing the textile industry and leading to the expansion of railways. This era brought about unprecedented economic growth and urbanization, fundamentally altering social structures and paving the way for the modern capitalist system, despite also causing significant social inequalities and poor working conditions initially.",
        "flowread_html": '<span class="token">The</span><span class="token"> Industrial</span><span class="token highlighted"> Revolution</span><span class="token">,</span><span class="token"> which</span><span class="token"> began</span><span class="token"> in</span><span class="token"> Britain</span><span class="token"> in</span><span class="token"> the</span><span class="token"> late</span><span class="token"> </span><span class="token">1</span><span class="token">8</span><span class="token">th</span><span class="token"> century</span><span class="token">,</span><span class="token"> marked</span><span class="token"> a</span><span class="token"> profound</span><span class="token"> turning</span><span class="token"> point</span><span class="token"> in</span><span class="token"> human</span><span class="token"> history</span><span class="token">.</span><span class="token"> It</span><span class="token"> initiated</span><span class="token"> the</span><span class="token"> transition</span><span class="token"> from</span><span class="token"> agrarian</span><span class="token">,</span><span class="token"> handic</span><span class="token">raft</span><span class="token"> economies</span><span class="token"> to</span><span class="token"> industry</span><span class="token"> and</span><span class="token"> machine</span><span class="token"> manufacturing</span><span class="token">.</span><span class="token"> The</span><span class="token"> invention</span><span class="token"> of</span><span class="token"> the</span><span class="token"> steam</span><span class="token"> engine</span><span class="token">,</span><span class="token"> pioneered</span><span class="token"> by</span><span class="token"> figures</span><span class="token"> like</span><span class="token"> James</span><span class="token"> Watt</span><span class="token">,</span><span class="token"> dramatically</span><span class="token"> increased</span><span class="token"> the</span><span class="token"> efficiency</span><span class="token"> of</span><span class="token"> factories</span><span class="token"> and</span><span class="token"> transportation</span><span class="token">,</span><span class="token"> revolution</span><span class="token">izing</span><span class="token"> the</span><span class="token"> textile</span><span class="token"> industry</span><span class="token"> and</span><span class="token"> leading</span><span class="token"> to</span><span class="token"> the</span><span class="token"> expansion</span><span class="token"> of</span><span class="token"> railways</span><span class="token">.</span><span class="token"> This</span><span class="token"> era</span><span class="token"> brought</span><span class="token"> about</span><span class="token"> unprecedented</span><span class="token"> economic</span><span class="token"> growth</span><span class="token"> and</span><span class="token"> urbanization</span><span class="token">,</span><span class="token"> fundamentally</span><span class="token"> altering</span><span class="token"> social</span><span class="token"> structures</span><span class="token"> and</span><span class="token"> paving</span><span class="token"> the</span><span class="token"> way</span><span class="token"> for</span><span class="token"> the</span><span class="token"> modern</span><span class="token"> capitalist</span><span class="token"> system</span><span class="token">,</span><span class="token"> despite</span><span class="token"> also</span><span class="token"> causing</span><span class="token"> significant</span><span class="token"> social</span><span class="token"> inequalities</span><span class="token"> and</span><span class="token"> poor</span><span class="token"> working</span><span class="token"> conditions</span><span class="token"> initially</span><span class="token">.</span>',
        "questions": [
            {
                "question": "Where did the Industrial Revolution begin?",
                "options": ["United States", "France", "Germany", "Britain"],
                "correct": 3
            },
            {
                "question": "Which invention dramatically increased factory efficiency?",
                "options": ["The cotton gin", "The telegraph", "The steam engine", "The assembly line"],
                "correct": 2
            }
        ]
    }
]

# --- Study API Endpoints ---
@app.get("/api/study/texts")
def get_study_texts():
    return {"texts": STUDY_TEXTS}

class StudySubmission(BaseModel):
    user_id: str
    text_id: int
    condition: str
    reading_time_ms: int
    score: int
    total_questions: int

@app.post("/api/study/submit")
def submit_study_result(submission: StudySubmission):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO study_results (user_id, text_id, condition, reading_time_ms, score, total_questions) VALUES (?, ?, ?, ?, ?, ?)",
        (submission.user_id, submission.text_id, submission.condition, submission.reading_time_ms, submission.score, submission.total_questions)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/study/stats")
def get_study_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Calculate stats for plain
    c.execute("SELECT AVG(reading_time_ms), AVG(CAST(score AS FLOAT) / total_questions) * 100, COUNT(*) FROM study_results WHERE condition = 'plain'")
    plain_stats = c.fetchone()
    
    # Calculate stats for flowread
    c.execute("SELECT AVG(reading_time_ms), AVG(CAST(score AS FLOAT) / total_questions) * 100, COUNT(*) FROM study_results WHERE condition = 'flowread'")
    flowread_stats = c.fetchone()
    
    conn.close()
    
    return {
        "plain": {
            "avg_reading_time_ms": plain_stats[0] or 0,
            "avg_accuracy_percent": plain_stats[1] or 0,
            "sample_size": plain_stats[2]
        },
        "flowread": {
            "avg_reading_time_ms": flowread_stats[0] or 0,
            "avg_accuracy_percent": flowread_stats[1] or 0,
            "sample_size": flowread_stats[2]
        }
    }

# --- Saliency API (Existing) ---
model_id = "google/gemma-2b"

# Load the model and tokenizer globally.
# Use MPS if available, otherwise CPU. MPS (Metal Performance Shaders) works well on modern Macs.
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Loading {model_id} on {device}...")

try:
    hf_token = os.environ.get("HF_TOKEN")
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",
        token=hf_token
    ).to(device)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Make sure you are logged into Hugging Face and have access to the Gemma model.")
    print("Run `huggingface-cli login` in your terminal.")

class TextRequest(BaseModel):
    text: str
    layers: Optional[List[int]] = None  # List of layer indices to average
    preprompt: str = ""    # Optional task-driven intent

@app.post("/analyze")
async def analyze_text(request: TextRequest):
    text = request.text
    preprompt = request.preprompt.strip()
    
    if not text.strip():
        return {"tokens": [], "scores": []}

    # Combine preprompt and text if preprompt exists
    full_text = f"{preprompt}\n\n{text}" if preprompt else text

    inputs = tokenizer(full_text, return_tensors="pt").to(device)
    
    with torch.no_grad():
        # Ensure we ask the model to output attentions explicitly
        outputs = model(**inputs, output_attentions=True)
        
    # Check if attentions are actually returned
    if not outputs.attentions:
        print("Warning: Model did not return attentions.")
        return {"words": []}
        
    num_layers = len(outputs.attentions)
    
    selected_layers = request.layers
    if not selected_layers:
        start_layer = num_layers // 4
        end_layer = num_layers - (num_layers // 4)
        selected_layers = list(range(start_layer, end_layer))
        
    selected_layers = [l for l in selected_layers if 0 <= l < num_layers]
    if not selected_layers:
        selected_layers = [num_layers - 1]
        
    stacked_attentions = torch.stack([outputs.attentions[l] for l in selected_layers])
    avg_attention = stacked_attentions.mean(dim=(0, 2))[0] 
    
    # Calculate importance: sum of attention each token *receives* from the sequence
    importance = avg_attention.sum(dim=0).cpu().float().numpy()
    
    if len(importance) > 1:
        # Normalize to 0-1, optionally excluding the first token (<bos>) from max/min calculation
        # as <bos> often has very high attention, skewing the rest
        min_score = importance[1:].min()
        max_score = importance[1:].max()
        
        normalized_scores = (importance - min_score) / (max_score - min_score)
        # Keep <bos> at max score
        normalized_scores[0] = 1.0
        normalized_scores = normalized_scores.clip(0, 1)
    else:
        normalized_scores = [1.0] * len(importance)
        
    input_ids = inputs["input_ids"][0].tolist()
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    
    result = []
    for i, t in enumerate(tokens):
        # Decode properly
        word = tokenizer.decode([input_ids[i]])
        # Special check for Gemma, decoding often removes spaces incorrectly or leaves tokens empty
        # Let's clean the raw token just in case
        raw_clean = t.replace('\u2581', ' ')
        
        # We will pass both decoded word and raw cleaned token to frontend to help render
        result.append({
            "token": raw_clean,
            "word": word,
            "score": float(normalized_scores[i])
        })
        
    return {"words": result}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)