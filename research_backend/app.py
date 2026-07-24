from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import requests
import re
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="WriteSense AI – Research Paper Identification",
    description="Abstract-based domain-aware research recommendation system",
    version="4.0"
)

# ---------------- CORS ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- CONFIG ----------------

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3"
CROSSREF_API = "https://api.crossref.org/works"

# ---------------- REQUEST MODEL ----------------

class PaperTextRequest(BaseModel):
    text: str
    year_from: Optional[int] = None
    year_to: Optional[int] = None

# ---------------- OLLAMA CALL ---------------------

def call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False #Return full response at once
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=180)
    response.raise_for_status()
    return response.json()["response"]

# ---------------- SAFE JSON PARSER ----------------
#Looks for JSON inside AI output
#Checks if it exists
#Converts it into usable Python format
# Stops safely if something is wrong


def safe_json_from_llm(raw: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise HTTPException(status_code=500, detail="LLM did not return valid JSON")

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse JSON from LLM output")

# ---------------- ABSTRACT EXTRACTION ----------------

def extract_abstract_only(text: str) -> str:
    """
    Extract abstract based on heading 'ABSTRACT'
    until next section heading.
    """

    text_lower = text.lower()

    # Find "abstract"
    start = text_lower.find("abstract")
    if start == -1:
        return text[:1500] #Just return the first 1500 characters of the document.(fallback method)

    # Extract from abstract onwards
    abstract_part = text[start:start + 2000]

    # Stop at next section-like word
    stop_words = ["introduction", "1.", "keywords"]
    for word in stop_words:
        idx = abstract_part.lower().find(word)
        if idx > 50:
            return abstract_part[:idx].strip()

    return abstract_part.strip()

# ---------------- KEYWORD EXTRACTION ----------------

def extract_keywords_from_document(text: str) -> dict:

    prompt = f"""
You are a research domain analyzer.

Extract 5–8 core technical terms defining the research problem.
Return STRICT JSON only:

{{
  "primary_domain": "...",
  "sub_domains": ["...", "..."],
  "keywords": ["term1", "term2"]
}}


Document Abstract:
\"\"\"{text}\"\"\"
"""

    raw = call_ollama(prompt)
    return safe_json_from_llm(raw)


# ---------------- RELEVANCE SCORING ----------------------

def compute_relevance_score(paper: dict, keywords: List[str], primary_domain: str) -> float:

    score = 0
    title = paper.get("title", "").lower()
    abstract = (paper.get("abstract") or "").lower()
    year = paper.get("year", 0)

    # Keyword in title (strong)
    for kw in keywords:
        if kw.lower() in title:
            score += 5

    # Keyword in abstract (medium)
    for kw in keywords:
        if kw.lower() in abstract:
            score += 2

    # Primary domain match
    if primary_domain.lower() in title:
        score += 8

    # Recency boost
    if year:
        score += (year - 2000) * 0.05

    return score

# ---------------- IEEE CITATION ----------------

def format_ieee_citation(index: int, paper: dict) -> str:

    authors = paper.get("authors", "")
    title = paper.get("title", "")
    venue = paper.get("venue", "")
    year = paper.get("year", "")
    doi = paper.get("doi", "")

    citation = f"[{index}] "

    if authors:
        author_text = ", ".join(authors[:3])
        if len(authors) > 3:
            author_text += ", et al."
        citation += f"{author_text}, "

    citation += f"“{title},” "

    if venue:
        citation += f"{venue}, "

    if year:
        citation += f"{year}"

    citation += "." #Every citation ends with period.

    if doi:
        citation += f" doi: {doi}"

    return citation

# ---------------- CROSSREF SEARCH ----------------

def search_crossref(
    keywords: List[str],
    primary_domain: str,
    year_from: Optional[int],
    year_to: Optional[int]
) -> List[dict]:

    query = primary_domain + " " + " ".join(keywords[:4])

    params = {
        "query": query,
        "rows": 100
    }

    response = requests.get(
        CROSSREF_API,
        params=params,
        timeout=30,
        headers={"User-Agent": "WriteSense-AI (mailto:demo@email.com)"}
    )

    response.raise_for_status()
    data = response.json()

    papers = []

    allowed_types = {
        "journal-article",
        "proceedings-article",
        "book-chapter"
    }

    for item in data.get("message", {}).get("items", []): #This goes through each paper returned by Crossref.

        if item.get("type") not in allowed_types:
            continue

        title_list = item.get("title", []) #no title ->skip
        if not title_list:
            continue

        title = title_list[0]

        year = None
        if "issued" in item and "date-parts" in item["issued"]:  #no year ->skip
            parts = item["issued"]["date-parts"]
            if parts and parts[0]:
                year = parts[0][0]

        if not year:
            continue

        if year_from and year < year_from:
            continue
        if year_to and year > year_to:
            continue

        authors = []
        for a in item.get("author", []):
            given = a.get("given", "") #Get the author's first name.
            family = a.get("family", "") #Get the author's last name.
            name = f"{given} {family}".strip()
            if name:
                authors.append(name)

        if not authors:
            continue

        paper = {
            "title": title,
            "authors": authors,
            "year": year,
            "venue": item.get("container-title", [""])[0] if item.get("container-title") else "",
            "doi": item.get("DOI"),
            "url": item.get("URL", "#"),
            "abstract": item.get("abstract", "")
        }

        papers.append(paper)

    # Compute relevance scores
    for paper in papers:
        paper["relevance_score"] = compute_relevance_score(
            paper,
            keywords,
            primary_domain
        )

    # Sort by highest relevance
    papers.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Limit top 20
    papers = papers[:20]

    # Add citations and clean
    for i, paper in enumerate(papers):
        paper["ieee_citation"] = format_ieee_citation(i + 1, paper)
        paper.pop("relevance_score", None)
        paper.pop("abstract", None)

    return papers

# ---------------- MAIN ENDPOINT ----------------

@app.post("/research/find")
def find_related_research(req: PaperTextRequest):

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Empty document text")

    # 🔥 Extract abstract only
    abstract_text = extract_abstract_only(req.text)

    print("\n========== ABSTRACT USED FOR ANALYSIS ==========")
    print(abstract_text[:500])
    print("===============================================\n")

    keyword_data = extract_keywords_from_document(abstract_text)

    papers = search_crossref(
        keyword_data["keywords"],
        keyword_data["primary_domain"],
        req.year_from,
        req.year_to
    )

    return {
        "analysis": keyword_data,
        "related_papers": papers
    }
    
