import numpy as np

# Lazy-loaded transformer model
_MODEL = None

ANCHORS = {
    "Dizziness": [
        "feeling dizzy", "dizziness", "lightheaded", "room is spinning", 
        "unsteady", "vertigo", "giddiness", "faintness", "loss of balance"
    ],
    "Headache": [
        "headache", "throbbing head", "head is pounding", "migraine", 
        "splitting headache", "head pain", "pressure in my head"
    ],
    "MuscleCramps": [
        "muscle cramps", "cramping", "muscle spasms", "painful contractions", 
        "stiff legs", "body cramps", "charley horse"
    ],
    "Nausea": [
        "nausea", "feeling nauseous", "want to vomit", "sick to my stomach", 
        "throwing up", "indigestion", "retching"
    ],
    "Confusion": [
        "confusion", "disoriented", "cannot think clearly", "hallucinations", 
        "delirious", "acting strange", "slurred speech", "feeling lost"
    ]
}

EXTRA_KEYWORDS = {
    "Dizziness": ["dizzy", "light headed", "faint", "fainting"],
    "Headache": ["head hurts", "head ache"],
    "MuscleCramps": ["cramps", "leg cramps", "calf cramps", "spasm"],
    "Nausea": ["nauseous", "vomit", "vomiting", "queasy"],
    "Confusion": ["confused", "not thinking clearly", "slurring", "delirium"]
}

# Pre-computed anchor embeddings (cached once model is loaded)
_ANCHOR_EMBEDDINGS = {}

KEYWORD_TERMS = {
    symptom: sorted(
        set(phrase.lower() for phrase in phrases + EXTRA_KEYWORDS.get(symptom, [])),
        key=len,
        reverse=True
    )
    for symptom, phrases in ANCHORS.items()
}

METHOD_LABELS = {
    "semantic": "Semantic transformer",
    "keyword": "Keyword fallback"
}

def get_model_and_anchors():
    global _MODEL, _ANCHOR_EMBEDDINGS
    if _MODEL is None:
        print("Loading local SentenceTransformer 'all-MiniLM-L6-v2' (approx. 80MB)...")
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Precompute embeddings for all anchor phrases
        for symptom, phrases in ANCHORS.items():
            _ANCHOR_EMBEDDINGS[symptom] = _MODEL.encode(phrases, convert_to_numpy=True)
            
    return _MODEL, _ANCHOR_EMBEDDINGS

def cosine_similarity(a, b):
    # a: (dim,), b: (num_anchors, dim)
    dot_product = np.dot(b, a)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b, axis=1)
    return dot_product / (norm_a * norm_b + 1e-8)

def _empty_result(method="semantic", message="No symptom text provided."):
    return {
        "flags": {sym: 0 for sym in ANCHORS.keys()},
        "scores": {sym: 0.0 for sym in ANCHORS.keys()},
        "method": method,
        "method_label": METHOD_LABELS.get(method, method),
        "message": message,
        "matches": {sym: [] for sym in ANCHORS.keys()}
    }

def extract_symptoms_keyword(clinical_text):
    """Fallback parser that detects known symptom phrases without ML downloads."""
    text = f" {clinical_text.lower()} "
    flags = {}
    scores = {}
    matches = {}

    for symptom, terms in KEYWORD_TERMS.items():
        symptom_matches = [term for term in terms if term in text]
        match_count = len(symptom_matches)
        flags[symptom] = 1 if match_count > 0 else 0
        scores[symptom] = round(min(1.0, match_count / 2), 3)
        matches[symptom] = symptom_matches[:3]

    return {
        "flags": flags,
        "scores": scores,
        "method": "keyword",
        "method_label": METHOD_LABELS["keyword"],
        "message": "Parsed with keyword fallback. Review detections before using them.",
        "matches": matches
    }

def extract_symptoms(clinical_text, threshold=0.40):
    """
    Parses natural language symptoms, computing cosine similarity against 
    anchor phrases for each clinical category.
    Returns a dict with detected symptom flags and best match scores.
    """
    if not clinical_text or clinical_text.strip() == "":
        return _empty_result()

    try:
        model, anchor_embeddings = get_model_and_anchors()
        query_emb = model.encode(clinical_text, convert_to_numpy=True)
    except Exception as exc:
        fallback = extract_symptoms_keyword(clinical_text)
        fallback["message"] = f"Transformer parser unavailable; used keyword fallback. Details: {exc}"
        return fallback
    
    flags = {}
    scores = {}
    matches = {}
    
    for symptom, embeddings in anchor_embeddings.items():
        # Compute cosine similarity between query and all anchor embeddings for this symptom
        sims = cosine_similarity(query_emb, embeddings)
        max_sim = float(np.max(sims))
        best_idx = int(np.argmax(sims))
        
        scores[symptom] = round(max_sim, 3)
        flags[symptom] = 1 if max_sim >= threshold else 0
        matches[symptom] = [ANCHORS[symptom][best_idx]]
        
    return {
        "flags": flags,
        "scores": scores,
        "method": "semantic",
        "method_label": METHOD_LABELS["semantic"],
        "message": "Semantic symptom parsing completed. Review detections before using them.",
        "matches": matches
    }
