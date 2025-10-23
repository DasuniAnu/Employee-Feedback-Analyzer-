from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import torch
from typing import Dict, List

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
except Exception:
    nlp = None

load_dotenv = lambda: None
try:
    from dotenv import load_dotenv as _ld
    _ld()
except Exception:
    pass

gemini_api_key = os.getenv('GOOGLE_API_KEY') or 'AIzaSyC2vCvUu3PL6KtVwWA4ZSaFYf283VMSFUs'
gemini_model = None
if genai is not None and gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception:
        gemini_model = None

app = FastAPI(title='NLP Agent (Gemini Only)')

class Inp(BaseModel):
    text: str

# Theme classification labels
classifier_labels = [
    'Compensation', 'Workload', 'Management', 'Culture', 'Benefits',
    'Career Growth', 'Work-life Balance', 'Recognition', 'Communication', 'Other'
]

def _normalize_theme(raw: str) -> str:
    key = (raw or '').strip().lower()
    # Map common variants to canonical labels
    if any(k in key for k in ['salary', 'pay', 'compensation', 'bonus']):
        return 'Compensation'
    if any(k in key for k in ['manager', 'lead', 'supervisor', 'leadership']):
        return 'Management'
    if any(k in key for k in ['hr', 'human resources']):
        return 'HR'
    if any(k in key for k in ['workload', 'overtime', 'hours', 'deadline', 'pressure']):
        return 'Workload'
    if any(k in key for k in ['benefit', 'health', 'insurance', 'perk']):
        return 'Benefits'
    if any(k in key for k in ['culture', 'environment', 'inclusive', 'toxic', 'diversity', 'company culture']):
        return 'Culture'
    if any(k in key for k in ['career', 'promotion', 'growth', 'development']):
        return 'Career Growth'
    if any(k in key for k in ['work-life', 'balance', 'flexible', 'remote']):
        return 'Work-life Balance'
    if any(k in key for k in ['recognition', 'appreciation', 'credit']):
        return 'Recognition'
    if any(k in key for k in ['communication', 'transparenc', 'communicat']):
        return 'Communication'
    return 'Other'

def _split_by_themes_with_rules(text: str) -> Dict[str, List[str]]:
    themes_map: Dict[str, List[str]] = {
        'Compensation': [], 'Management': [], 'HR': [], 'Workload': [], 'Culture': [], 'Benefits': [],
        'Career Growth': [], 'Work-life Balance': [], 'Recognition': [], 'Communication': [], 'Other': []
    }
    # naive sentence split by punctuation
    import re
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    for s in sentences:
        normalized = _normalize_theme(s)
        themes_map.setdefault(normalized, []).append(s)
    # remove empty lists
    return {k: v for k, v in themes_map.items() if v}

def _gemini_theme_split(text: str) -> Dict[str, List[str]]:
    if gemini_model is None:
        return {}
    try:
        prompt = (
            "Split the feedback into sentences and group them by HR-related themes. "
            "Return ONLY JSON with keys as themes and values as arrays of sentences. "
            "Use concise theme names like Compensation, Management, HR, Workload, Culture, Benefits, "
            "Career Growth, Work-life Balance, Recognition, Communication, Other.\n\nFeedback:\n" + text
        )
        resp = gemini_model.generate_content(prompt)
        import json, re
        txt = (resp.text or '').strip()
        try:
            data = json.loads(txt)
        except Exception:
            m = re.search(r"\{[\s\S]*\}", txt)
            data = json.loads(m.group(0)) if m else {}
        # ensure list-of-strings and normalize keys
        out: Dict[str, List[str]] = {}
        for k, v in (data.items() if isinstance(data, dict) else []):
            if isinstance(v, list):
                canon = _normalize_theme(k)
                out.setdefault(canon, [])
                out[canon].extend([str(s).strip() for s in v if str(s).strip()])
        return out
    except Exception:
        return {}

def _gemini_classify_theme(text: str) -> Dict:
    """Use Gemini for theme classification"""
    if gemini_model is None:
        return {}
    try:
        prompt = f"""
        Classify the following employee feedback into one of these HR themes: {', '.join(classifier_labels)}
        
        Return ONLY a JSON object with:
        - "label": the best matching theme
        - "score": confidence score (0.0-1.0)
        - "scores": object with all theme scores
        
        Feedback: "{text}"
        
        JSON format:
        {{"label": "Compensation", "score": 0.85, "scores": {{"Compensation": 0.85, "Management": 0.1, ...}}}}
        """
        
        resp = gemini_model.generate_content(prompt)
        import json, re
        txt = (resp.text or '').strip()
        try:
            data = json.loads(txt)
        except Exception:
            m = re.search(r"\{[\s\S]*\}", txt)
            data = json.loads(m.group(0)) if m else {}
        
        if isinstance(data, dict) and 'label' in data:
            return {
                'label': data.get('label', 'Other'),
                'score': float(data.get('score', 0.5)),
                'scores': data.get('scores', {}),
                'model': 'Gemini'
            }
    except Exception:
        pass
    return {}

@app.post('/themes')
async def themes(inp: Inp):
    summary = ''

    # Use Gemini for summarization
    if gemini_model is not None:
        try:
            prompt = (
                "Summarize the main themes of the following employee feedback in 1 concise sentence.\n\n"
                + inp.text + "\n\nReturn only the sentence."
            )
            r = gemini_model.generate_content(prompt)
            summary = (r.text or '').strip()
        except Exception:
            summary = inp.text[:140]

    # Last resort heuristic
    if not summary:
        summary = inp.text[:140]

    # Extract entities using spaCy
    ents = []
    if nlp is not None:
        try:
            doc = nlp(inp.text)
            ents = sorted({ent.text for ent in doc.ents})
        except Exception:
            ents = []

    # Use Gemini for theme classification
    classification = _gemini_classify_theme(inp.text)
    if not classification:
        # Fallback to rule-based classification
        classification = {
            'label': 'Other',
            'score': 0.5,
            'scores': {},
            'model': 'Rule-based'
        }

    # Theme-based sentence grouping: prefer Gemini, fallback to rules
    theme_sentences = _gemini_theme_split(inp.text)
    theme_source = "Gemini" if theme_sentences else "Rule-based"
    if not theme_sentences:
        theme_sentences = _split_by_themes_with_rules(inp.text)

    return {
        'summary': summary, 
        'entities': ents, 
        'classification': classification, 
        'theme_sentences': theme_sentences,
        'theme_source': theme_source,
        'gemini_available': gemini_model is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
