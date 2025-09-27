from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import torch

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from transformers import pipeline
    from huggingface_hub import login
except Exception:
    pipeline = None
    login = None

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

client = None
if OpenAI is not None and os.getenv('OPENAI_API_KEY'):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = FastAPI(title='NLP Agent (HF summarization + spaCy, OpenAI fallback)')

class Inp(BaseModel):
    text: str

# Optional: Zero-shot classifier for theme labeling (configurable)
classifier = None
classifier_labels: list[str] = []
classifier_model_name = os.getenv('NLP_CLASSIFIER_MODEL', 'facebook/bart-large-mnli')
labels_env = os.getenv('NLP_CLASSIFIER_LABELS', '')
if labels_env:
    classifier_labels = [lbl.strip() for lbl in labels_env.split(',') if lbl.strip()]
else:
    # Reasonable defaults; override with NLP_CLASSIFIER_LABELS
    classifier_labels = [
        'Compensation', 'Workload', 'Management', 'Culture', 'Benefits',
        'Career Growth', 'Work-life Balance', 'Recognition', 'Communication', 'Other'
    ]

try:
    if pipeline is not None and classifier_labels:
        hf_token = (
            os.getenv('HUGGINGFACE_TOKEN')
            or os.getenv('HUGGINGFACEHUB_API_TOKEN')
            or os.getenv('HF_TOKEN')
        )
        if hf_token and login is not None:
            try:
                os.environ['HUGGINGFACEHUB_API_TOKEN'] = hf_token
                login(token=hf_token)
            except Exception:
                pass

        classifier = pipeline(
            'zero-shot-classification',
            model=classifier_model_name,
            device=0 if torch.cuda.is_available() else -1
        )
except Exception:
    classifier = None

@app.post('/themes')
async def themes(inp: Inp):
    summary = ''

    # Prefer Hugging Face summarization if available
    used_hf = False
    if pipeline is not None:
        try:
            hf_token = (
                os.getenv('HUGGINGFACE_TOKEN')
                or os.getenv('HUGGINGFACEHUB_API_TOKEN')
                or os.getenv('HF_TOKEN')
            )
            if hf_token and login is not None:
                try:
                    os.environ['HUGGINGFACEHUB_API_TOKEN'] = hf_token
                    login(token=hf_token)
                except Exception:
                    pass

            summarizer = pipeline(
                'summarization',
                model='sshleifer/distilbart-cnn-12-6',
                device=0 if torch.cuda.is_available() else -1
            )
            # Keep it to a single concise sentence
            result = summarizer(inp.text, max_length=40, min_length=8, do_sample=False)
            summary = (result[0]['summary_text'] or '').strip()
            used_hf = True
        except Exception:
            used_hf = False

    # If HF unavailable, try OpenAI
    if not used_hf and client is not None:
        try:
            prompt = (
                "Summarize the main themes of the following employee feedback in 1 concise sentence.\n\n"
                + inp.text
                + "\n\nReturn only the summary sentence."
            )
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role':'user','content':prompt}],
                temperature=0.2
            )
            summary = (resp.choices[0].message.content or '').strip()
        except Exception:
            summary = inp.text[:140]

    # Last resort heuristic
    if not summary:
        summary = inp.text[:140]

    ents = []
    if nlp is not None:
        try:
            doc = nlp(inp.text)
            ents = sorted({ent.text for ent in doc.ents})
        except Exception:
            ents = []
    classification = {}
    if classifier is not None and classifier_labels:
        try:
            # Use a simple template; configurable via env in the future if needed
            res = classifier(inp.text, candidate_labels=classifier_labels, hypothesis_template='This feedback is about {}.')
            # Build scores map
            scores_map = {label: float(score) for label, score in zip(res['labels'], res['scores'])}
            top_label = res['labels'][0] if res.get('labels') else ''
            top_score = float(res['scores'][0]) if res.get('scores') else 0.0
            classification = {
                'label': top_label,
                'score': top_score,
                'scores': scores_map,
                'model': classifier_model_name
            }
        except Exception:
            classification = {}

    return {'summary': summary, 'entities': ents, 'classification': classification}
