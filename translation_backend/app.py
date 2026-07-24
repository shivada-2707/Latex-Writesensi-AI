from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from fastapi.middleware.cors import CORSMiddleware
import re

# ================= FASTAPI APP =================

app = FastAPI(title="WriteSense AI - Translation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ================= LOAD MODEL =================

model_name = "facebook/nllb-200-distilled-600M"

print("Loading translation model...")

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

print("Model loaded successfully")

# ================= LANGUAGE MAP =================

language_map = {
    "Malayalam": "mal_Mlym",
    "Hindi": "hin_Deva",
    "Tamil": "tam_Taml",
    "Telugu": "tel_Telu",
    "Kannada": "kan_Knda",
    "Bengali": "ben_Beng",
    "Marathi": "mar_Deva",
    "Gujarati": "guj_Gujr",
    "Punjabi": "pan_Guru",
    "Urdu": "urd_Arab",
    "French": "fra_Latn",
    "German": "deu_Latn",
    "Spanish": "spa_Latn",
    "Italian": "ita_Latn",
    "Portuguese": "por_Latn",
    "Dutch": "nld_Latn",
    "Greek": "ell_Grek",
    "Polish": "pol_Latn",
    "Czech": "ces_Latn",
    "Romanian": "ron_Latn",
    "Russian": "rus_Cyrl",
    "Ukrainian": "ukr_Cyrl",
    "Chinese": "zho_Hans",
    "Japanese": "jpn_Jpan",
    "Korean": "kor_Hang",
    "Thai": "tha_Thai",
    "Vietnamese": "vie_Latn",
    "Indonesian": "ind_Latn",
    "Malay": "zsm_Latn",
    "Arabic": "arb_Arab",
    "Hebrew": "heb_Hebr",
    "Turkish": "tur_Latn",
    "Persian": "pes_Arab",
    "Swahili": "swh_Latn",
    "Zulu": "zul_Latn"
}

# ================= REQUEST MODEL =================

class TranslationRequest(BaseModel):
    text: str
    language: str

# ================= CLEAN TEXT =================

def clean_text(text: str):

    # Remove LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+', '', text)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Split sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    seen = set()
    unique = []

    for s in sentences:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            unique.append(s)

    return " ".join(unique)

# ================= TRANSLATE FUNCTION =================

def translate_text(text: str, target_lang: str):

    target_lang_code = language_map.get(target_lang)

    if not target_lang_code:
        return "Unsupported language"

    tokenizer.src_lang = "eng_Latn"

    text = clean_text(text)

    sentences = re.split(r'(?<=[.!?])\s+', text)

    translated_sentences = []

    for sentence in sentences:

        if not sentence.strip():
            continue

        encoded = tokenizer(
            sentence,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        generated_tokens = model.generate(
            **encoded,
            forced_bos_token_id=tokenizer.convert_tokens_to_ids(target_lang_code),
            max_length=256,
            num_beams=4
        )

        translated = tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True
        )[0]

        translated_sentences.append(translated)

    return "\n\n".join(translated_sentences)

# ================= API ENDPOINT =================

@app.post("/translate")
def translate(req: TranslationRequest):

    try:

        if not req.text.strip():
            return {"translation": "Empty text"}

        translated = translate_text(req.text, req.language)

        return {"translation": translated}

    except Exception as e:

        print("Translation error:", e)

        return {"translation": "Translation failed"}
