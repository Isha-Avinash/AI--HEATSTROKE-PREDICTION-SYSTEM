import numpy as np
import os

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

# Pre-computed anchor embeddings (cached once model is loaded)
_ANCHOR_EMBEDDINGS = {}

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

def extract_symptoms(clinical_text, threshold=0.40):
    """
    Parses natural language symptoms, computing cosine similarity against 
    anchor phrases for each clinical category.
    Returns a dict with detected symptom flags and best match scores.
    """
    if not clinical_text or clinical_text.strip() == "":
        return {
            "flags": {sym: 0 for sym in ANCHORS.keys()},
            "scores": {sym: 0.0 for sym in ANCHORS.keys()}
        }
        
    model, anchor_embeddings = get_model_and_anchors()
    
    # Encode user query
    query_emb = model.encode(clinical_text, convert_to_numpy=True)
    
    flags = {}
    scores = {}
    
    for symptom, embeddings in anchor_embeddings.items():
        # Compute cosine similarity between query and all anchor embeddings for this symptom
        sims = cosine_similarity(query_emb, embeddings)
        max_sim = float(np.max(sims))
        
        scores[symptom] = round(max_sim, 3)
        flags[symptom] = 1 if max_sim >= threshold else 0
        
    return {
        "flags": flags,
        "scores": scores
    }
