from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import login

load_dotenv = lambda: None
try:
    from dotenv import load_dotenv as _ld
    _ld()
except Exception:
    pass

# Initialize Hugging Face sentiment analysis pipeline
sentiment_pipeline = None
try:
    # Use a pre-trained sentiment analysis model
    model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    
    # Retrieve Hugging Face token from common env var names and login
    hf_token = (
        os.getenv('HUGGINGFACE_TOKEN')
        or os.getenv('HUGGINGFACEHUB_API_TOKEN')
        or os.getenv('HF_TOKEN')
    )
    if hf_token:
        # Ensure the hub picks it up
        os.environ['HUGGINGFACEHUB_API_TOKEN'] = hf_token
        try:
            login(token=hf_token)
        except Exception:
            # If login fails, environment variable is still enough for transformers
            pass
    
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model=model_name,
        tokenizer=model_name,
        device=0 if torch.cuda.is_available() else -1
    )
    print("Hugging Face sentiment analysis model loaded successfully!")
except Exception as e:
    print(f"Failed to load Hugging Face model: {e}")
    sentiment_pipeline = None

app = FastAPI(title='Sentiment Agent (Hugging Face)')

class Inp(BaseModel):
    text: str

@app.post('/analyze')
async def analyze(inp: Inp):
    def heuristic(txt: str):
        t = txt.lower()
        score = 0.0
        label = 'Neutral'
        if any(w in t for w in ['good','great','happy','satisfied','love']):
            label = 'Positive'; score = 0.9
        if any(w in t for w in ['bad','stress','angry','hate','frustrat']):
            label = 'Negative'; score = 0.9
        return {'label': label, 'score': score}

    if sentiment_pipeline is None:
        return heuristic(inp.text)

    try:
        # Analyze sentiment using Hugging Face pipeline
        result = sentiment_pipeline(inp.text)
        
        # Map Hugging Face labels to our expected format
        hf_label = result[0]['label']
        hf_score = result[0]['score']
        
        # Convert label mapping (LABEL_0=negative, LABEL_1=neutral, LABEL_2=positive)
        if hf_label == 'LABEL_0':
            label = 'Negative'
        elif hf_label == 'LABEL_1':
            label = 'Neutral'
        elif hf_label == 'LABEL_2':
            label = 'Positive'
        else:
            label = 'Neutral'
        
        return {'label': label, 'score': hf_score}
        
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return heuristic(inp.text)
