import torch
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
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

@app.get("/")
def read_root():
    return RedirectResponse(url="/static/index.html")

# --- SQLite Database Setup ---
# Hugging Face Spaces make the /app directory read-only by default.
# We must write the database to /data (if persistent storage is enabled) or /tmp.
DB_DIR = "/data" if os.path.exists("/data") else "/tmp"
DB_FILE = os.path.join(DB_DIR, "study.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS study_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            text_id INTEGER,
            condition TEXT, -- "plain" or "flowread" or "gradient"
            reading_time_ms INTEGER,
            score INTEGER,
            total_questions INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS study_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            preference TEXT, -- "plain", "flowread", or "gradient"
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
        "questions": [
            {
                "question": "Approximately how many neurons are in the human brain?",
                "options": [
                    "86 million",
                    "86 billion",
                    "100 trillion",
                    "50 billion"
                ],
                "correct": 1
            },
            {
                "question": "What is the term for the brain's ability to reorganize itself?",
                "options": [
                    "Synaptic generation",
                    "Neurogenesis",
                    "Neuroplasticity",
                    "Cognitive adaptation"
                ],
                "correct": 2
            }
        ],
        "flowread_html": "<span class=\"token highlighted\">The</span><span class=\"token highlighted\"> human</span><span class=\"token highlighted\"> brain</span><span class=\"token highlighted\"> is</span><span class=\"token highlighted\"> a</span><span class=\"token highlighted\"> marvel</span><span class=\"token\"> of</span><span class=\"token highlighted\"> biological</span><span class=\"token highlighted\"> engineering</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> containing</span><span class=\"token\"> approximately</span><span class=\"token\"> </span><span class=\"token\">8</span><span class=\"token\">6</span><span class=\"token highlighted\"> billion</span><span class=\"token highlighted\"> neurons</span><span class=\"token highlighted\"> interconnected</span><span class=\"token highlighted\"> by</span><span class=\"token\"> tri</span><span class=\"token\">lli</span><span class=\"token\">ons</span><span class=\"token\"> of</span><span class=\"token highlighted\"> synapses</span><span class=\"token highlighted\">.</span><span class=\"token highlighted\"> These</span><span class=\"token highlighted\"> neural</span><span class=\"token highlighted\"> networks</span><span class=\"token\"> are</span><span class=\"token\"> responsible</span><span class=\"token highlighted\"> for</span><span class=\"token\"> everything</span><span class=\"token highlighted\"> from</span><span class=\"token highlighted\"> basic</span><span class=\"token highlighted\"> autonomic</span><span class=\"token highlighted\"> functions</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> like</span><span class=\"token\"> breathing</span><span class=\"token\"> and</span><span class=\"token\"> heart</span><span class=\"token\"> rate</span><span class=\"token\">,</span><span class=\"token highlighted\"> to</span><span class=\"token\"> complex</span><span class=\"token highlighted\"> cognitive</span><span class=\"token\"> processes</span><span class=\"token\"> such</span><span class=\"token\"> as</span><span class=\"token highlighted\"> memory</span><span class=\"token highlighted\">,</span><span class=\"token\"> emotion</span><span class=\"token\">,</span><span class=\"token\"> and</span><span class=\"token highlighted\"> problem</span><span class=\"token highlighted\">-</span><span class=\"token highlighted\">solving</span><span class=\"token highlighted\">.</span><span class=\"token highlighted\"> Neurop</span><span class=\"token highlighted\">lastic</span><span class=\"token highlighted\">ity</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> the</span><span class=\"token highlighted\"> brain</span><span class=\"token highlighted\">'</span><span class=\"token highlighted\">s</span><span class=\"token\"> ability</span><span class=\"token\"> to</span><span class=\"token highlighted\"> reorgan</span><span class=\"token highlighted\">ize</span><span class=\"token\"> itself</span><span class=\"token\"> by</span><span class=\"token\"> forming</span><span class=\"token\"> new</span><span class=\"token\"> neural</span><span class=\"token\"> connections</span><span class=\"token\"> throughout</span><span class=\"token highlighted\"> life</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> allows</span><span class=\"token highlighted\"> humans</span><span class=\"token\"> to</span><span class=\"token highlighted\"> learn</span><span class=\"token\"> new</span><span class=\"token\"> skills</span><span class=\"token\">,</span><span class=\"token\"> recover</span><span class=\"token\"> from</span><span class=\"token\"> injuries</span><span class=\"token\">,</span><span class=\"token\"> and</span><span class=\"token\"> adapt</span><span class=\"token\"> to</span><span class=\"token\"> changing</span><span class=\"token highlighted\"> environments</span><span class=\"token highlighted\">.</span><span class=\"token\"> This</span><span class=\"token\"> extraordinary</span><span class=\"token highlighted\"> adaptability</span><span class=\"token\"> is</span><span class=\"token\"> what</span><span class=\"token\"> makes</span><span class=\"token\"> our</span><span class=\"token\"> species</span><span class=\"token\"> so</span><span class=\"token\"> resilient</span><span class=\"token\"> and</span><span class=\"token\"> capable</span><span class=\"token\"> of</span><span class=\"token\"> continuous</span><span class=\"token\"> intellectual</span><span class=\"token\"> growth</span><span class=\"token\">.</span>",
        "flowread_gradient_html": "<span class=\"token\" style=\"opacity: 0.53; font-weight: 489;\">The</span><span class=\"token\" style=\"opacity: 0.56; font-weight: 506;\"> human</span><span class=\"token\" style=\"opacity: 1.00; font-weight: 800;\"> brain</span><span class=\"token\" style=\"opacity: 0.54; font-weight: 490;\"> is</span><span class=\"token\" style=\"opacity: 0.51; font-weight: 472;\"> a</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 489;\"> marvel</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 452;\"> of</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 484;\"> biological</span><span class=\"token\" style=\"opacity: 0.55; font-weight: 498;\"> engineering</span><span class=\"token\" style=\"opacity: 0.55; font-weight: 498;\">,</span><span class=\"token\" style=\"opacity: 0.56; font-weight: 506;\"> containing</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 455;\"> approximately</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 455;\"> </span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\">8</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\">6</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 469;\"> billion</span><span class=\"token\" style=\"opacity: 0.71; font-weight: 608;\"> neurons</span><span class=\"token\" style=\"opacity: 0.55; font-weight: 500;\"> interconnected</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 484;\"> by</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 419;\"> tri</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 419;\">lli</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 419;\">ons</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 413;\"> of</span><span class=\"token\" style=\"opacity: 0.72; font-weight: 613;\"> synapses</span><span class=\"token\" style=\"opacity: 0.72; font-weight: 613;\">.</span><span class=\"token\" style=\"opacity: 0.51; font-weight: 472;\"> These</span><span class=\"token\" style=\"opacity: 0.57; font-weight: 516;\"> neural</span><span class=\"token\" style=\"opacity: 0.57; font-weight: 515;\"> networks</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 455;\"> are</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 452;\"> responsible</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 482;\"> for</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 464;\"> everything</span><span class=\"token\" style=\"opacity: 0.59; font-weight: 529;\"> from</span><span class=\"token\" style=\"opacity: 0.51; font-weight: 474;\"> basic</span><span class=\"token\" style=\"opacity: 0.56; font-weight: 504;\"> autonomic</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 482;\"> functions</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 482;\">,</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 481;\"> like</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 466;\"> breathing</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 444;\"> and</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 424;\"> heart</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 435;\"> rate</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 435;\">,</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 479;\"> to</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 462;\"> complex</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 487;\"> cognitive</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 451;\"> processes</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 432;\"> such</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 451;\"> as</span><span class=\"token\" style=\"opacity: 0.51; font-weight: 474;\"> memory</span><span class=\"token\" style=\"opacity: 0.51; font-weight: 474;\">,</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 450;\"> emotion</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 450;\">,</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 428;\"> and</span><span class=\"token\" style=\"opacity: 0.64; font-weight: 559;\"> problem</span><span class=\"token\" style=\"opacity: 0.64; font-weight: 559;\">-</span><span class=\"token\" style=\"opacity: 0.64; font-weight: 559;\">solving</span><span class=\"token\" style=\"opacity: 0.64; font-weight: 559;\">.</span><span class=\"token\" style=\"opacity: 0.68; font-weight: 587;\"> Neurop</span><span class=\"token\" style=\"opacity: 0.68; font-weight: 587;\">lastic</span><span class=\"token\" style=\"opacity: 0.68; font-weight: 587;\">ity</span><span class=\"token\" style=\"opacity: 0.68; font-weight: 587;\">,</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 469;\"> the</span><span class=\"token\" style=\"opacity: 0.59; font-weight: 527;\"> brain</span><span class=\"token\" style=\"opacity: 0.59; font-weight: 527;\">'</span><span class=\"token\" style=\"opacity: 0.59; font-weight: 527;\">s</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 434;\"> ability</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 464;\"> to</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 469;\"> reorgan</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 469;\">ize</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 444;\"> itself</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 454;\"> by</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 434;\"> forming</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 431;\"> new</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 426;\"> neural</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 433;\"> connections</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 426;\"> throughout</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 480;\"> life</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 480;\">,</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 485;\"> allows</span><span class=\"token\" style=\"opacity: 0.54; font-weight: 493;\"> humans</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 463;\"> to</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 482;\"> learn</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 433;\"> new</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 454;\"> skills</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 454;\">,</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 449;\"> recover</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> from</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 438;\"> injuries</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 438;\">,</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 433;\"> and</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 436;\"> adapt</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\"> to</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 414;\"> changing</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 485;\"> environments</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 485;\">.</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> This</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 442;\"> extraordinary</span><span class=\"token\" style=\"opacity: 0.51; font-weight: 472;\"> adaptability</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 428;\"> is</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 435;\"> what</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 443;\"> makes</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 428;\"> our</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 468;\"> species</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 430;\"> so</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 443;\"> resilient</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 427;\"> and</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 412;\"> capable</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 422;\"> of</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 420;\"> continuous</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 413;\"> intellectual</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 403;\"> growth</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 403;\">.</span>"
    },
    {
        "id": 2,
        "topic": "History",
        "text": "The Industrial Revolution, which began in Britain in the late 18th century, marked a profound turning point in human history. It initiated the transition from agrarian, handicraft economies to industry and machine manufacturing. The invention of the steam engine, pioneered by figures like James Watt, dramatically increased the efficiency of factories and transportation, revolutionizing the textile industry and leading to the expansion of railways. This era brought about unprecedented economic growth and urbanization, fundamentally altering social structures and paving the way for the modern capitalist system, despite also causing significant social inequalities and poor working conditions initially.",
        "questions": [
            {
                "question": "Where did the Industrial Revolution begin?",
                "options": [
                    "United States",
                    "France",
                    "Germany",
                    "Britain"
                ],
                "correct": 3
            },
            {
                "question": "Which invention dramatically increased factory efficiency?",
                "options": [
                    "The cotton gin",
                    "The telegraph",
                    "The steam engine",
                    "The assembly line"
                ],
                "correct": 2
            }
        ],
        "flowread_html": "<span class=\"token highlighted\">The</span><span class=\"token highlighted\"> Industrial</span><span class=\"token highlighted\"> Revolution</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> which</span><span class=\"token highlighted\"> began</span><span class=\"token\"> in</span><span class=\"token highlighted\"> Britain</span><span class=\"token\"> in</span><span class=\"token\"> the</span><span class=\"token\"> late</span><span class=\"token\"> </span><span class=\"token highlighted\">1</span><span class=\"token highlighted\">8</span><span class=\"token highlighted\">th</span><span class=\"token highlighted\"> century</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> marked</span><span class=\"token\"> a</span><span class=\"token highlighted\"> profound</span><span class=\"token\"> turning</span><span class=\"token highlighted\"> point</span><span class=\"token\"> in</span><span class=\"token highlighted\"> human</span><span class=\"token highlighted\"> history</span><span class=\"token highlighted\">.</span><span class=\"token highlighted\"> It</span><span class=\"token highlighted\"> initiated</span><span class=\"token\"> the</span><span class=\"token\"> transition</span><span class=\"token highlighted\"> from</span><span class=\"token highlighted\"> agrarian</span><span class=\"token highlighted\">,</span><span class=\"token\"> handic</span><span class=\"token\">raft</span><span class=\"token highlighted\"> economies</span><span class=\"token highlighted\"> to</span><span class=\"token highlighted\"> industry</span><span class=\"token\"> and</span><span class=\"token highlighted\"> machine</span><span class=\"token highlighted\"> manufacturing</span><span class=\"token highlighted\">.</span><span class=\"token highlighted\"> The</span><span class=\"token highlighted\"> invention</span><span class=\"token highlighted\"> of</span><span class=\"token\"> the</span><span class=\"token highlighted\"> steam</span><span class=\"token highlighted\"> engine</span><span class=\"token highlighted\">,</span><span class=\"token\"> pioneered</span><span class=\"token highlighted\"> by</span><span class=\"token\"> figures</span><span class=\"token\"> like</span><span class=\"token\"> James</span><span class=\"token\"> Watt</span><span class=\"token\">,</span><span class=\"token highlighted\"> dramatically</span><span class=\"token highlighted\"> increased</span><span class=\"token\"> the</span><span class=\"token\"> efficiency</span><span class=\"token\"> of</span><span class=\"token highlighted\"> factories</span><span class=\"token\"> and</span><span class=\"token highlighted\"> transportation</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> revolution</span><span class=\"token highlighted\">izing</span><span class=\"token\"> the</span><span class=\"token\"> textile</span><span class=\"token\"> industry</span><span class=\"token\"> and</span><span class=\"token\"> leading</span><span class=\"token\"> to</span><span class=\"token\"> the</span><span class=\"token\"> expansion</span><span class=\"token\"> of</span><span class=\"token highlighted\"> railways</span><span class=\"token highlighted\">.</span><span class=\"token\"> This</span><span class=\"token highlighted\"> era</span><span class=\"token highlighted\"> brought</span><span class=\"token\"> about</span><span class=\"token\"> unprecedented</span><span class=\"token highlighted\"> economic</span><span class=\"token highlighted\"> growth</span><span class=\"token\"> and</span><span class=\"token highlighted\"> urbanization</span><span class=\"token highlighted\">,</span><span class=\"token\"> fundamentally</span><span class=\"token highlighted\"> altering</span><span class=\"token\"> social</span><span class=\"token\"> structures</span><span class=\"token\"> and</span><span class=\"token\"> paving</span><span class=\"token\"> the</span><span class=\"token\"> way</span><span class=\"token\"> for</span><span class=\"token\"> the</span><span class=\"token\"> modern</span><span class=\"token\"> capitalist</span><span class=\"token\"> system</span><span class=\"token\">,</span><span class=\"token\"> despite</span><span class=\"token\"> also</span><span class=\"token\"> causing</span><span class=\"token\"> significant</span><span class=\"token\"> social</span><span class=\"token\"> inequalities</span><span class=\"token\"> and</span><span class=\"token\"> poor</span><span class=\"token\"> working</span><span class=\"token\"> conditions</span><span class=\"token\"> initially</span><span class=\"token\">.</span>",
        "flowread_gradient_html": "<span class=\"token\" style=\"opacity: 0.49; font-weight: 462;\">The</span><span class=\"token\" style=\"opacity: 0.59; font-weight: 524;\"> Industrial</span><span class=\"token\" style=\"opacity: 1.00; font-weight: 800;\"> Revolution</span><span class=\"token\" style=\"opacity: 1.00; font-weight: 800;\">,</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 456;\"> which</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 467;\"> began</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 430;\"> in</span><span class=\"token\" style=\"opacity: 0.58; font-weight: 519;\"> Britain</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> in</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 410;\"> the</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 418;\"> late</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 415;\"> </span><span class=\"token\" style=\"opacity: 0.49; font-weight: 457;\">1</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 457;\">8</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 457;\">th</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 467;\"> century</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 467;\">,</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 460;\"> marked</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 422;\"> a</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 439;\"> profound</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 418;\"> turning</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 440;\"> point</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 423;\"> in</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 447;\"> human</span><span class=\"token\" style=\"opacity: 0.57; font-weight: 511;\"> history</span><span class=\"token\" style=\"opacity: 0.57; font-weight: 511;\">.</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 456;\"> It</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 450;\"> initiated</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 431;\"> the</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 426;\"> transition</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 444;\"> from</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 469;\"> agrarian</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 469;\">,</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 433;\"> handic</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 433;\">raft</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 451;\"> economies</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 452;\"> to</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 489;\"> industry</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 432;\"> and</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 444;\"> machine</span><span class=\"token\" style=\"opacity: 0.55; font-weight: 498;\"> manufacturing</span><span class=\"token\" style=\"opacity: 0.55; font-weight: 498;\">.</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 461;\"> The</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 442;\"> invention</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 440;\"> of</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 417;\"> the</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 465;\"> steam</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 483;\"> engine</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 483;\">,</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 434;\"> pioneered</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 436;\"> by</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\"> figures</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 426;\"> like</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 414;\"> James</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 428;\"> Watt</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 428;\">,</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 437;\"> dramatically</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 445;\"> increased</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\"> the</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 432;\"> efficiency</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\"> of</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 467;\"> factories</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 432;\"> and</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 442;\"> transportation</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 442;\">,</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\"> revolution</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\">izing</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 415;\"> the</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 436;\"> textile</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 428;\"> industry</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 433;\"> and</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 416;\"> leading</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 425;\"> to</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 409;\"> the</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 413;\"> expansion</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 407;\"> of</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 468;\"> railways</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 468;\">.</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 423;\"> This</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 454;\"> era</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 447;\"> brought</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 418;\"> about</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 434;\"> unprecedented</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 438;\"> economic</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 437;\"> growth</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 431;\"> and</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 449;\"> urbanization</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 449;\">,</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 424;\"> fundamentally</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 441;\"> altering</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 432;\"> social</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 427;\"> structures</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 432;\"> and</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 419;\"> paving</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 407;\"> the</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 410;\"> way</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 423;\"> for</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 409;\"> the</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 422;\"> modern</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> capitalist</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 415;\"> system</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 415;\">,</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 432;\"> despite</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 417;\"> also</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 431;\"> causing</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 419;\"> significant</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 416;\"> social</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> inequalities</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 415;\"> and</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 414;\"> poor</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 407;\"> working</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 406;\"> conditions</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 403;\"> initially</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 403;\">.</span>"
    },
    {
        "id": 3,
        "topic": "Technology",
        "text": "The James Webb Space Telescope is the largest and most powerful space telescope ever built. Launched in 2021, it operates primarily in the infrared spectrum, allowing it to peer through dense cosmic dust and observe the universe's most distant, early galaxies. Unlike its predecessor, Hubble, JWST orbits the Sun at the second Lagrange point, keeping it constantly shielded from the Sun's heat and light by its massive sunshield. This incredibly cold environment is necessary to prevent the telescope's own infrared emissions from interfering with its highly sensitive observations of exoplanet atmospheres and star formation.",
        "questions": [
            {
                "question": "What spectrum does the James Webb Space Telescope primarily operate in?",
                "options": [
                    "Ultraviolet",
                    "X-ray",
                    "Infrared",
                    "Visible light"
                ],
                "correct": 2
            },
            {
                "question": "Where does the telescope orbit to stay cold?",
                "options": [
                    "Low Earth Orbit",
                    "The Moon's orbit",
                    "The first Lagrange point",
                    "The second Lagrange point"
                ],
                "correct": 3
            }
        ],
        "flowread_html": "<span class=\"token highlighted\">The</span><span class=\"token\"> James</span><span class=\"token highlighted\"> Webb</span><span class=\"token highlighted\"> Space</span><span class=\"token highlighted\"> Telescope</span><span class=\"token highlighted\"> is</span><span class=\"token highlighted\"> the</span><span class=\"token highlighted\"> largest</span><span class=\"token\"> and</span><span class=\"token\"> most</span><span class=\"token highlighted\"> powerful</span><span class=\"token highlighted\"> space</span><span class=\"token highlighted\"> telescope</span><span class=\"token\"> ever</span><span class=\"token highlighted\"> built</span><span class=\"token highlighted\">.</span><span class=\"token highlighted\"> Launched</span><span class=\"token\"> in</span><span class=\"token\"> </span><span class=\"token highlighted\">2</span><span class=\"token highlighted\">0</span><span class=\"token highlighted\">2</span><span class=\"token highlighted\">1</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> it</span><span class=\"token highlighted\"> operates</span><span class=\"token\"> primarily</span><span class=\"token\"> in</span><span class=\"token\"> the</span><span class=\"token highlighted\"> infrared</span><span class=\"token highlighted\"> spectrum</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> allowing</span><span class=\"token\"> it</span><span class=\"token\"> to</span><span class=\"token\"> peer</span><span class=\"token\"> through</span><span class=\"token\"> dense</span><span class=\"token highlighted\"> cosmic</span><span class=\"token\"> dust</span><span class=\"token\"> and</span><span class=\"token highlighted\"> observe</span><span class=\"token\"> the</span><span class=\"token highlighted\"> universe</span><span class=\"token highlighted\">'</span><span class=\"token highlighted\">s</span><span class=\"token\"> most</span><span class=\"token\"> distant</span><span class=\"token\">,</span><span class=\"token\"> early</span><span class=\"token highlighted\"> galaxies</span><span class=\"token highlighted\">.</span><span class=\"token highlighted\"> Unlike</span><span class=\"token\"> its</span><span class=\"token\"> predecessor</span><span class=\"token\">,</span><span class=\"token highlighted\"> Hubble</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> JW</span><span class=\"token highlighted\">ST</span><span class=\"token highlighted\"> orbits</span><span class=\"token\"> the</span><span class=\"token highlighted\"> Sun</span><span class=\"token highlighted\"> at</span><span class=\"token\"> the</span><span class=\"token\"> second</span><span class=\"token highlighted\"> Lagrange</span><span class=\"token highlighted\"> point</span><span class=\"token highlighted\">,</span><span class=\"token highlighted\"> keeping</span><span class=\"token\"> it</span><span class=\"token\"> constantly</span><span class=\"token highlighted\"> shielded</span><span class=\"token highlighted\"> from</span><span class=\"token\"> the</span><span class=\"token highlighted\"> Sun</span><span class=\"token highlighted\">'</span><span class=\"token highlighted\">s</span><span class=\"token\"> heat</span><span class=\"token\"> and</span><span class=\"token\"> light</span><span class=\"token\"> by</span><span class=\"token\"> its</span><span class=\"token\"> massive</span><span class=\"token highlighted\"> sun</span><span class=\"token highlighted\">shield</span><span class=\"token highlighted\">.</span><span class=\"token\"> This</span><span class=\"token\"> incredibly</span><span class=\"token highlighted\"> cold</span><span class=\"token\"> environment</span><span class=\"token\"> is</span><span class=\"token\"> necessary</span><span class=\"token\"> to</span><span class=\"token highlighted\"> prevent</span><span class=\"token\"> the</span><span class=\"token highlighted\"> telescope</span><span class=\"token highlighted\">'</span><span class=\"token highlighted\">s</span><span class=\"token\"> own</span><span class=\"token\"> infrared</span><span class=\"token\"> emissions</span><span class=\"token\"> from</span><span class=\"token\"> interfering</span><span class=\"token\"> with</span><span class=\"token\"> its</span><span class=\"token\"> highly</span><span class=\"token\"> sensitive</span><span class=\"token\"> observations</span><span class=\"token\"> of</span><span class=\"token\"> ex</span><span class=\"token\">oplan</span><span class=\"token\">et</span><span class=\"token\"> atmospheres</span><span class=\"token\"> and</span><span class=\"token\"> star</span><span class=\"token\"> formation</span><span class=\"token\">.</span>",
        "flowread_gradient_html": "<span class=\"token\" style=\"opacity: 0.49; font-weight: 458;\">The</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 435;\"> James</span><span class=\"token\" style=\"opacity: 1.00; font-weight: 800;\"> Webb</span><span class=\"token\" style=\"opacity: 0.59; font-weight: 523;\"> Space</span><span class=\"token\" style=\"opacity: 0.75; font-weight: 632;\"> Telescope</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 478;\"> is</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 447;\"> the</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 463;\"> largest</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 423;\"> and</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 412;\"> most</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 443;\"> powerful</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 441;\"> space</span><span class=\"token\" style=\"opacity: 0.54; font-weight: 491;\"> telescope</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 422;\"> ever</span><span class=\"token\" style=\"opacity: 0.56; font-weight: 503;\"> built</span><span class=\"token\" style=\"opacity: 0.56; font-weight: 503;\">.</span><span class=\"token\" style=\"opacity: 0.51; font-weight: 475;\"> Launched</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\"> in</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 418;\"> </span><span class=\"token\" style=\"opacity: 0.50; font-weight: 463;\">2</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 463;\">0</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 463;\">2</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 463;\">1</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 463;\">,</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 452;\"> it</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 449;\"> operates</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 433;\"> primarily</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> in</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 418;\"> the</span><span class=\"token\" style=\"opacity: 0.57; font-weight: 510;\"> infrared</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\"> spectrum</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\">,</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 453;\"> allowing</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 420;\"> it</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 423;\"> to</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 437;\"> peer</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 437;\"> through</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 430;\"> dense</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 441;\"> cosmic</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 438;\"> dust</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 431;\"> and</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 458;\"> observe</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 439;\"> the</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 451;\"> universe</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 451;\">'</span><span class=\"token\" style=\"opacity: 0.48; font-weight: 451;\">s</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 414;\"> most</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 436;\"> distant</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 436;\">,</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 414;\"> early</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 478;\"> galaxies</span><span class=\"token\" style=\"opacity: 0.52; font-weight: 478;\">.</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 445;\"> Unlike</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 419;\"> its</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 437;\"> predecessor</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 437;\">,</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 467;\"> Hubble</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 467;\">,</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 468;\"> JW</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 468;\">ST</span><span class=\"token\" style=\"opacity: 0.55; font-weight: 496;\"> orbits</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 430;\"> the</span><span class=\"token\" style=\"opacity: 0.53; font-weight: 489;\"> Sun</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 441;\"> at</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 417;\"> the</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 415;\"> second</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 456;\"> Lagrange</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\"> point</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\">,</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 444;\"> keeping</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 431;\"> it</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 428;\"> constantly</span><span class=\"token\" style=\"opacity: 0.49; font-weight: 457;\"> shielded</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 445;\"> from</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 419;\"> the</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\"> Sun</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\">'</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\">s</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 438;\"> heat</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 423;\"> and</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 420;\"> light</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> by</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\"> its</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 418;\"> massive</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 465;\"> sun</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 465;\">shield</span><span class=\"token\" style=\"opacity: 0.50; font-weight: 465;\">.</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 422;\"> This</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 415;\"> incredibly</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 440;\"> cold</span><span class=\"token\" style=\"opacity: 0.46; font-weight: 439;\"> environment</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 414;\"> is</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 422;\"> necessary</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 431;\"> to</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 446;\"> prevent</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 420;\"> the</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 445;\"> telescope</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 445;\">'</span><span class=\"token\" style=\"opacity: 0.47; font-weight: 445;\">s</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> own</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> infrared</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 436;\"> emissions</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 414;\"> from</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 417;\"> interfering</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 419;\"> with</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 416;\"> its</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 407;\"> highly</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 417;\"> sensitive</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 421;\"> observations</span><span class=\"token\" style=\"opacity: 0.44; font-weight: 429;\"> of</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 430;\"> ex</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 430;\">oplan</span><span class=\"token\" style=\"opacity: 0.45; font-weight: 430;\">et</span><span class=\"token\" style=\"opacity: 0.43; font-weight: 418;\"> atmospheres</span><span class=\"token\" style=\"opacity: 0.42; font-weight: 413;\"> and</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 408;\"> star</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 403;\"> formation</span><span class=\"token\" style=\"opacity: 0.41; font-weight: 403;\">.</span>"
    }
]# --- Study API Endpoints ---
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

class StudyPreference(BaseModel):
    user_id: str
    preference: str

@app.post("/api/study/preference")
def submit_study_preference(submission: StudyPreference):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO study_preferences (user_id, preference) VALUES (?, ?)",
        (submission.user_id, submission.preference)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}

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
    
    # Calculate stats for gradient
    c.execute("SELECT AVG(reading_time_ms), AVG(CAST(score AS FLOAT) / total_questions) * 100, COUNT(*) FROM study_results WHERE condition = 'gradient'")
    gradient_stats = c.fetchone()
    
    # Calculate preferences
    c.execute("SELECT preference, COUNT(*) FROM study_preferences GROUP BY preference")
    preferences = dict(c.fetchall())
    
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
        },
        "gradient": {
            "avg_reading_time_ms": gradient_stats[0] or 0,
            "avg_accuracy_percent": gradient_stats[1] or 0,
            "sample_size": gradient_stats[2]
        },
        "preferences": preferences
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