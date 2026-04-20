import requests
import json

texts = [
    {
        "id": 1,
        "topic": "Science",
        "text": "The human brain is a marvel of biological engineering, containing approximately 86 billion neurons interconnected by trillions of synapses. These neural networks are responsible for everything from basic autonomic functions, like breathing and heart rate, to complex cognitive processes such as memory, emotion, and problem-solving. Neuroplasticity, the brain's ability to reorganize itself by forming new neural connections throughout life, allows humans to learn new skills, recover from injuries, and adapt to changing environments. This extraordinary adaptability is what makes our species so resilient and capable of continuous intellectual growth.",
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
    },
    {
        "id": 3,
        "topic": "Technology",
        "text": "The James Webb Space Telescope is the largest and most powerful space telescope ever built. Launched in 2021, it operates primarily in the infrared spectrum, allowing it to peer through dense cosmic dust and observe the universe's most distant, early galaxies. Unlike its predecessor, Hubble, JWST orbits the Sun at the second Lagrange point, keeping it constantly shielded from the Sun's heat and light by its massive sunshield. This incredibly cold environment is necessary to prevent the telescope's own infrared emissions from interfering with its highly sensitive observations of exoplanet atmospheres and star formation.",
        "questions": [
            {
                "question": "What spectrum does the James Webb Space Telescope primarily operate in?",
                "options": ["Ultraviolet", "X-ray", "Infrared", "Visible light"],
                "correct": 2
            },
            {
                "question": "Where does the telescope orbit to stay cold?",
                "options": ["Low Earth Orbit", "The Moon's orbit", "The first Lagrange point", "The second Lagrange point"],
                "correct": 3
            }
        ]
    }
]

for t in texts:
    res = requests.post("http://localhost:7860/analyze", json={"text": t["text"], "layers": [4,5,6,7,8,9,10,11,12,13]})
    data = res.json()
    
    words = []
    current_word = []
    current_max = 0
    
    for i, item in enumerate(data["words"]):
        if i == 0 and ("<bos>" in item["token"] or "<bos>" in item["word"]):
            continue
            
        token_str = item["token"]
        is_whitespace = (token_str.strip() == '')
        prev_is_whitespace = (current_word[-1]["token"].strip() == '') if len(current_word) > 0 else False
        
        if token_str.startswith(" ") or (len(current_word) > 0 and is_whitespace != prev_is_whitespace):
            if len(current_word) > 0:
                words.append({"tokens": current_word, "max_score": current_max})
            current_word = [item]
            current_max = item["score"]
        else:
            current_word.append(item)
            current_max = max(current_max, item["score"])
            
    if len(current_word) > 0:
         words.append({"tokens": current_word, "max_score": current_max})
         
    word_scores = [w["max_score"] for w in words]
    word_scores.sort()
    threshold_idx = int(len(word_scores) * 0.60)
    threshold = word_scores[threshold_idx] if len(word_scores) > 0 else 0
    
    binary_html = ""
    gradient_html = ""
    
    for w in words:
        # Binary
        className = "token highlighted" if w["max_score"] >= threshold else "token"
        for item in w["tokens"]:
            binary_html += f'<span class="{className}">{item["token"]}</span>'
            
        # Gradient
        opacity = 0.4 + (w["max_score"] * 0.6)
        weight = 400 + int(w["max_score"] * 400)
        for item in w["tokens"]:
            gradient_html += f'<span class="token" style="opacity: {opacity:.2f}; font-weight: {weight};">{item["token"]}</span>'
            
    t["flowread_html"] = binary_html
    t["flowread_gradient_html"] = gradient_html

with open("study_texts.json", "w") as f:
    json.dump(texts, f, indent=4)
print("Saved to study_texts.json")
