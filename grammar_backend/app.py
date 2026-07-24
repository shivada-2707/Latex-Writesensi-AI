from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import requests
import re
import difflib

app = FastAPI()

# ================= CORS =======================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= CONFIG =================

LANGUAGETOOL_URL = "http://127.0.0.1:8081/v2/check"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3"

# ================= MODEL =================

class GrammarRequest(BaseModel):
    text: str


# ================= HELPER FUNCTIONS =================

def extract_latex(text: str):
    latex_commands = []
#function scans the input text using a reg express to identify latexi mean l
    def replacer(match):
        latex_commands.append(match.group())
        return f"__LATEX_{len(latex_commands)-1}__"
#Find something → Replace it.
    cleaned = re.sub(
        r"(\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?)",
        replacer,
        text
    )

    return cleaned, latex_commands


def restore_latex(text: str, latex_commands: List[str]):
    for i, cmd in enumerate(latex_commands):
        text = text.replace(f"__LATEX_{i}__", cmd)
    return text

# otherwise it think like  it is a puctuation mistake 
def inside_citation(text: str, offset: int):
    citation_pattern = r"\[[0-9]+\]"
    for match in re.finditer(citation_pattern, text):
        if match.start() <= offset <= match.end():
            return True
    return False


# ================= RULE-BASED GRAMMAR =================

@app.post("/grammar/check")
def check_grammar(req: GrammarRequest):

    original_text = req.text.strip()

    if not original_text:
        raise HTTPException(status_code=400, detail="Empty text")

    original_text = original_text.replace("\u00A0", " ")#special invisible space.

    text, latex_cmds = extract_latex(original_text)
    #__LATEX_0__ This are bad.
    #calling lange tool
    try:
        response = requests.post(
            LANGUAGETOOL_URL,
            data={
                "text": text,
                "language": "en-US",
                "enabledCategories": "GRAMMAR,PUNCTUATION,TYPOGRAPHY,STYLE"
            },
            timeout=30
        )
        #If server error → stop
        response.raise_for_status()
        lt_data = response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LanguageTool error: {str(e)}")

    matches = [] #We create empty list to store grammar errors.

    for m in lt_data.get("matches", []):

        offset = m.get("offset", 0)
        length = m.get("length", 0)

        if inside_citation(text, offset):
            continue
    
        replacement = None
        if m.get("replacements"):
            replacement = m["replacements"][0]["value"]
            #Save Error Details
        matches.append({
            "offset": offset,
            "length": length,
            "error_word": text[offset:offset+length],
            "message": m.get("message"),
            "replacement": replacement,
            "rule": m.get("rule", {}).get("id", ""),
            "category": m.get("rule", {}).get("category", {}).get("name", "")
        })

    restored_text = restore_latex(text, latex_cmds)

    return {
        "original_text": restored_text,
        "matches": matches
    }


# ================= AI GRAMMAR CORRECTION =================

@app.post("/grammar/ai-improve")
def ai_improve(req: GrammarRequest):

    original_text = req.text.strip()

    if not original_text:
        raise HTTPException(status_code=400, detail="Empty text")

    protected_segments = []

    def protect(match):
        protected_segments.append(match.group(0))
        return f"__PROTECTED_{len(protected_segments)-1}__"

    # Protect LaTeX, citations, math, et al.
    text = re.sub(r"(\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?)", protect, original_text)
    text = re.sub(r"\[[0-9]+\]", protect, text)
    text = re.sub(r"\$.*?\$", protect, text)
    text = re.sub(r"\bet al\.", protect, text)

    prompt = f"""
You are a strict academic grammar correction engine.

Fix ALL grammar mistakes including:
- verb tense
- subject-verb agreement
- article usage
- plural/singular
- preposition errors
- punctuation

STRICT RULES:
- DO NOT explain anything
- DO NOT add bullet points
- DO NOT add commentary
- DO NOT describe corrections
- DO NOT add headings
- DO NOT rewrite meaning
- Only fix grammar

Return ONLY the corrected paragraph.
Return nothing else.

Text:
{text}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "top_p": 0.7
                }
            },
            timeout=120
        )

        response.raise_for_status()
        data = response.json()

        improved = data.get("response", "").strip()

        # Remove explanations if model misbehaves
        improved = re.split(
            r"Corrected errors:|Explanation:|Changes:",
            improved
        )[0].strip()

        # Remove bullet lines
        improved = "\n".join(
            line for line in improved.splitlines()
            if not line.strip().startswith(("*", "-", "•"))
        ).strip()

        # Restore protected content
        for i, segment in enumerate(protected_segments):
            improved = improved.replace(f"__PROTECTED_{i}__", segment)

        # Diff detection
        original_words = original_text.split()
        improved_words = improved.split()

        diff = list(difflib.ndiff(original_words, improved_words))
# Detect word-level changes

        changes = []
        removed = None

        for d in diff:
            if d.startswith("- "):
                removed = d[2:]
            elif d.startswith("+ ") and removed:
                changes.append({
                    "error_word": removed,
                    "correction": d[2:]
                })
                removed = None

        return {
            "improved_text": improved,
            "ai_changes": changes
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")
