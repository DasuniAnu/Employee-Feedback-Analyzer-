from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import torch

try:
    from transformers import pipeline
    from huggingface_hub import login
except Exception:
    pipeline = None
    login = None

load_dotenv = lambda: None
try:
    from dotenv import load_dotenv as _ld
    _ld()
except Exception:
    pass

app = FastAPI(title='Urgency Agent (HF zero-shot + heuristic)')

class Inp(BaseModel):
    text: str

def heuristic_urgency(txt: str) -> dict:
    """Fallback urgency detection using keyword matching"""
    t = (txt or '').lower().strip()
    
    # High urgency keywords
    high_urgency = {
        'urgent', 'emergency', 'critical', 'immediate', 'asap', 'crisis', 'serious',
        'harassment', 'discrimination', 'bullying', 'threat', 'danger', 'unsafe',
        'quit', 'leaving', 'resign', 'fire', 'terminate', 'sue', 'legal', 'lawyer',
        'mental health', 'depression', 'anxiety', 'suicide', 'self-harm'
    }
    
    # Medium urgency keywords
    medium_urgency = {
        'concern', 'worried', 'problem', 'issue', 'complaint', 'unhappy', 'frustrated',
        'stress', 'overwhelmed', 'burnout', 'exhausted', 'tired', 'sick', 'illness',
        'conflict', 'disagreement', 'argument', 'fight', 'tension', 'hostile'
    }
    
    # Count urgency indicators
    high_count = sum(1 for word in high_urgency if word in t)
    medium_count = sum(1 for word in medium_urgency if word in t)
    
    if high_count > 0:
        return {'urgency': 'High', 'confidence': min(0.9, 0.6 + (high_count * 0.1)), 'reason': f'Contains {high_count} high-urgency keywords'}
    elif medium_count > 0:
        return {'urgency': 'Medium', 'confidence': min(0.8, 0.5 + (medium_count * 0.1)), 'reason': f'Contains {medium_count} medium-urgency keywords'}
    else:
        return {'urgency': 'Low', 'confidence': 0.7, 'reason': 'No urgency indicators detected'}

# Initialize Hugging Face zero-shot classifier
zeroshot = None
try:
    if pipeline is not None:
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

        # Use a robust zero-shot model for urgency classification
        model_name = 'facebook/bart-large-mnli'
        zeroshot = pipeline(
            'zero-shot-classification',
            model=model_name,
            device=0 if torch.cuda.is_available() else -1
        )
        print('Urgency Agent: Hugging Face zero-shot model loaded successfully!')
except Exception as e:
    print(f'Urgency Agent: failed to load HF model: {e}')
    zeroshot = None


    # Fallback to heuristic
    return heuristic_urgency(text)
