from fastapi import FastAPI
from pydantic import BaseModel
import requests
import re

app = FastAPI(title="WriteSense AI – LLaMA Summarization")


# ================= INPUT MODEL =================

class Document(BaseModel):
    text: str


# ================= CLEAN LATEX =================

def clean_latex(text):

    # remove LaTeX commands
    text = re.sub(r'\\cite\{.*?\}', '', text)
    text = re.sub(r'\\ref\{.*?\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)

    # remove braces
    text = text.replace("{", "").replace("}", "")

    # remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# ================= LLAMA SUMMARY =================
def llama_summary(text):

    prompt = f"""
Summarize the following text into a shorter version.

Rules:
- Keep the main idea only.
- Maximum 2 sentences only.
- Make it shorter than the original text.
- Do NOT repeat the original sentences.
- Return ONLY the summary.
- Dont add "Here is the summary"
- Dont add "Here is a 2-sentence summary"
- Dont add anything before the summary

Text:
{text}
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )

        data = response.json()

        summary = data.get("response", "").strip()

        # remove extra newlines
        summary = re.sub(r"\n+", " ", summary)

        return summary

    except Exception as e:
        print("LLaMA error:", e)
        return "Summary generation failed."

# ================= API =================

@app.post("/summary/document")
def summarize_document(doc: Document):

    text = doc.text

    # clean latex formatting
    cleaned_text = clean_latex(text)

    if len(cleaned_text) < 50:
        return {
            "section_summaries": {
                "Summary": "Selected text is too short to summarize."
            }
        }

    summary = llama_summary(cleaned_text)

    return {
        "section_summaries": {
            "Summary": summary
        }
    }
