from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import requests
import json

app = FastAPI(title="WriteSense Hybrid Clarity Engine")

# ================= CORS stup=================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = "llama3"

class TextRequest(BaseModel):
    text: str
# =====================================================
# ================= BASIC READABILITY =================
# =====================================================

def count_sentences(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    #To avoid division by zero later in formulas.
    return max(1, len(sentences))
    
#This finds all real words using regex.
def count_words(text):
    words = re.findall(r'\b\w+\b', text)
    return max(1, len(words))

def count_syllables(word):
    word = word.lower()
    word = re.sub(r'[^a-z]', '', word) #Remove anything that is not a letter.

    if len(word) <= 3:
        return 1

    vowels = "aeiouy"
    count = 0
    prev = False

    for char in word:
        if char in vowels:
            if not prev:
                count += 1
            prev = True
        else:
            prev = False

    if word.endswith("e"):
        count -= 1

    return max(1, count)

def total_syllables(text):
    words = re.findall(r'\b\w+\b', text)
    return sum(count_syllables(w) for w in words)

def compute_readability(text):
    sentences = count_sentences(text)
    words = count_words(text)
    syllables = total_syllables(text)

    avg_sentence_length = words / sentences
    avg_syllables_per_word = syllables / words

    fre = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    fre = round(max(0, min(100, fre)), 2)

    fkg = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
    fkg = round(max(0, fkg), 2)

    if fre >= 60:
        ease = "Standard readability."
    elif fre >= 30:
        ease = "Formal academic writing."
    else:
        ease = "Highly formal academic writing."

    if fkg <= 12:
        academic = "Undergraduate level."
    elif fkg <= 20:
        academic = "Postgraduate level."
    else:
        academic = "Research-level technical writing."

    return {
        "flesch_reading_ease": fre,
        "flesch_kincaid_grade": fkg,
        "reading_ease_explanation": ease,
        "academic_suitability": academic
    }


# =====================================================
# ================= ACADEMIC METRICS ==================
# =====================================================

COMMON_FUNCTION_WORDS = {
    "the","is","are","was","were","in","on","at","of","and","or","but",
    "to","for","with","as","by","an","a","that","this","it","from"
}

CLAUSE_MARKERS = [
    "because","although","while","since","that",
    "which","who","where","unless","whereas"
]

NOMINAL_SUFFIXES = [
    "tion","ment","ness","ity","ance","ence","ship"
]

def detect_passive(text):
    pattern = r'\b(am|is|are|was|were|be|been|being)\b\s+\b\w+ed\b'
    matches = re.findall(pattern, text.lower())
    return len(matches)

def lexical_density(text):
    words = re.findall(r'\b\w+\b', text.lower()) #Extract all words.
    total = len(words)
    content = [w for w in words if w not in COMMON_FUNCTION_WORDS]
    if total == 0:
        return 0
    return round((len(content) / total) * 100, 2)

def clause_density(text):
    sentences = count_sentences(text)
    text_lower = text.lower()
    count = 0
    for marker in CLAUSE_MARKERS:
        count += len(re.findall(r'\b' + marker + r'\b', text_lower))
    return round(count / sentences, 2)
    #Divide total clause markers by number of sentences.

def nominal_ratio(text):
#It checks how many words are nouns formed from verbs or adjectives.
    words = re.findall(r'\b\w+\b', text.lower())
    total = len(words)
    count = 0
    for w in words:
        for suf in NOMINAL_SUFFIXES:
            if w.endswith(suf):
                count += 1
                break
    if total == 0:
        return 0
    return round((count / total) * 100, 2)


@app.post("/clarity/academic")
def academic_clarity(req: TextRequest):

    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Empty text")

    sentences = count_sentences(text)
    passive_count = detect_passive(text)
    passive_percent = round((passive_count / max(1, sentences)) * 100, 2)

    if passive_percent > 60:
        passive_percent = 60 + (passive_percent - 60) * 0.3

    ld = lexical_density(text)
    cd = clause_density(text)
    nr = nominal_ratio(text)

    if passive_percent < 15:
        passive_interp = "Low passive usage (clear and direct)."
    elif passive_percent <= 30:
        passive_interp = "Balanced academic passive usage."
    else:
        passive_interp = "High passive usage (may reduce clarity)."

    if ld < 45:
        ld_interp = "Conversational writing."
    elif ld <= 60:
        ld_interp = "Academic-level lexical density."
    else:
        ld_interp = "Highly information-dense writing."

    if cd < 0.5:
        cd_interp = "Structurally simple sentences."
    elif cd <= 1.5:
        cd_interp = "Moderate structural complexity."
    else:
        cd_interp = "Highly complex clause embedding."

    if nr < 5:
        nr_interp = "Low abstraction."
    elif nr <= 12:
        nr_interp = "Balanced academic abstraction."
    else:
        nr_interp = "High nominalization (abstract style)."

    return {
        "metrics": {
            "passive_voice_percent": round(passive_percent, 2),
            "passive_interpretation": passive_interp,
            "lexical_density_percent": ld,
            "lexical_density_interpretation": ld_interp,
            "clause_density": cd,
            "clause_density_interpretation": cd_interp,
            "nominalization_ratio_percent": nr,
            "nominalization_interpretation": nr_interp
        }
    }


# =====================================================
# ================= OLLAMA CALL =======================
# =====================================================

def call_ollama(prompt, as_json=False):

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False, #👉 Return full response at once
        "options": {
            "temperature": 0.0, #0.0 → deterministic (same output every time)
            "top_p": 0.3 #Controls word selection diversity.
        }
    }

    # Only force JSON when needed
    if as_json:
        payload["format"] = "json"

    response = requests.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=120
    )

    if response.status_code != 200:
        raise RuntimeError("Ollama failed")

    return response.json()["response"]


# =====================================================
# ================= ANALYZE ===========================
# =====================================================

@app.post("/clarity/analyze")
def analyze_clarity(req: TextRequest):

    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Empty text")

    metrics = compute_readability(text)

    prompt = f"""
You are an academic writing evaluator.

Return only JSON.

{{
  "structure_quality": "High | Medium | Low",
  "structure_reason": "Explain structural organization in one clear sentence.",
  "tone_quality": "Excellent | Good | Moderate | Weak",
  "tone_reason": "Explain academic tone in one clear sentence.",
  "improvement_advice": "Provide a short academic improvement paragraph."
}}

Text:
\"\"\"{text}\"\"\"
"""

    try:
        raw = call_ollama(prompt, as_json=True)
        ai_data = json.loads(raw)

    except Exception as e:
        print("AI ERROR:", e)

        ai_data = {
            "structure_quality": "Medium",
            "structure_reason": "Automatic evaluation failed due to formatting issue.",
            "tone_quality": "Moderate",
            "tone_reason": "Automatic evaluation failed due to formatting issue.",
            "improvement_advice": "Consider simplifying long sentences."
        }

    return {
        "metrics": metrics,
        "ai_evaluation": ai_data
    }


# =====================================================
# ================= IMPROVE ===========================
# =====================================================

@app.post("/clarity/improve")
def improve_clarity(req: TextRequest):

    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Empty text")

    prompt = f"""
You are a professional academic editor.

Rewrite the following paragraph to improve clarity and academic tone.

IMPORTANT RULES:
- Return ONLY the improved paragraph.
- Do NOT repeat the original text.
- Do NOT include quotation marks.
- Do NOT include explanations.
- Do NOT include JSON.
- Do NOT wrap output in braces.

Text:
{text}
"""

    try:
        improved = call_ollama(prompt)
    except:
        raise HTTPException(500, "Improvement failed")

    # 🔥 BACKEND CLEANING (final protection)
    improved = improved.strip()
    improved = improved.replace("{", "").replace("}", "")
    improved = improved.strip('"').strip()

    return {
        "revised_text": improved
    }
