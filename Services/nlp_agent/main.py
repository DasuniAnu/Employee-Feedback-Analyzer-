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