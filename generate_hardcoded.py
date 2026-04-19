import requests

texts = [
    "The human brain is a marvel of biological engineering, containing approximately 86 billion neurons interconnected by trillions of synapses. These neural networks are responsible for everything from basic autonomic functions, like breathing and heart rate, to complex cognitive processes such as memory, emotion, and problem-solving. Neuroplasticity, the brain's ability to reorganize itself by forming new neural connections throughout life, allows humans to learn new skills, recover from injuries, and adapt to changing environments. This extraordinary adaptability is what makes our species so resilient and capable of continuous intellectual growth.",
    "The Industrial Revolution, which began in Britain in the late 18th century, marked a profound turning point in human history. It initiated the transition from agrarian, handicraft economies to industry and machine manufacturing. The invention of the steam engine, pioneered by figures like James Watt, dramatically increased the efficiency of factories and transportation, revolutionizing the textile industry and leading to the expansion of railways. This era brought about unprecedented economic growth and urbanization, fundamentally altering social structures and paving the way for the modern capitalist system, despite also causing significant social inequalities and poor working conditions initially."
]

htmls = []
for text in texts:
    res = requests.post("http://localhost:7860/analyze", json={"text": text, "layers": [4,5,6,7,8,9,10,11,12,13]})
    data = res.json()
    
    words = []
    current_word = []
    current_max = 0
    
    for i, item in enumerate(data["words"]):
        if i == 0 and ("<bos>" in item["token"] or "<bos>" in item["word"]):
            continue
        
        if item["token"].startswith(" ") and len(current_word) > 0:
            words.append({"tokens": current_word, "max_score": current_max})
            current_word = [item]
            current_max = item["score"]
        else:
            current_word.append(item)
            current_max = max(current_max, item["score"])
            
    if len(current_word) > 0:
         words.append({"tokens": current_word, "max_score": current_max})
    
    # Sort word scores to find the 40% highlight threshold
    word_scores = [w["max_score"] for w in words]
    word_scores.sort()
    threshold_idx = int(len(word_scores) * 0.60)
    threshold = word_scores[threshold_idx]
    
    html = ""
    for w in words:
        className = "token highlighted" if w["max_score"] >= threshold else "token"
        for item in w["tokens"]:
            html += f'<span class="{className}">{item["token"]}</span>'
            
    htmls.append(html)

print("====TEXT 1====")
print(htmls[0])
print("====TEXT 2====")
print(htmls[1])
