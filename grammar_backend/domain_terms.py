# domain_terms.py

DOMAIN_TERMS = {
    # Steganalysis / Security
    "steganalysis",
    "steganography",
    "cybersecurity",
    "forensics",
    "payload",
    "lsb",
    "dct",

    # ML / DL
    "cnn",
    "rnn",
    "resnet",
    "transformer",
    "vit",
    "gin",
    "gnn",
    "neural",
    "backpropagation",

    # Graphs
    "cfg",
    "control-flow",
    "control-flow-graph",
    "graph-based",
    "graph-level",

    # Programming
    "api",
    "fastapi",
    "uvicorn",
    "ollama",
    "llama",

    # LaTeX-safe words
    "latex",
    "overleaf"
}

def is_domain_term(word: str) -> bool:
    return word.lower().strip(".,()[]{}") in DOMAIN_TERMS

