from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import httpx
from shared.sanitize import sanitize_text
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Header

load_dotenv = lambda: None
try:
    from dotenv import load_dotenv as _ld
    _ld()
except Exception:
    pass

SENTIMENT_URL = os.getenv('SENTIMENT_URL','http://127.0.0.1:8001')
URGENCY_URL = os.getenv('URGENCY_URL','http://127.0.0.1:8007')
NLP_URL = os.getenv('NLP_URL','http://127.0.0.1:8002')
SUGGESTION_URL = os.getenv('SUGGESTION_URL','http://127.0.0.1:8003')
IR_URL = os.getenv('IR_URL','http://127.0.0.1:8004')
SEC_URL = os.getenv('SECURITY_URL','http://127.0.0.1:8005')

app = FastAPI(title='Orchestrator (API-first)')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:8080", "http://localhost:8080", "http://127.0.0.1:3000", "http://localhost:3000", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class In(BaseModel):
    text: str

async def post_json(url: str, payload: dict, headers: dict | None = None):
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

async def get_json(url: str, headers: dict | None = None):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()

@app.post('/analyze')
async def analyze(inp: In, authorization: str | None = Header(None)):
    # Verify token if provided
    if authorization:
        try:
            await get_json(f'{SEC_URL}/verify', headers={'Authorization': authorization})
        except Exception as e:
            raise HTTPException(401, f'Invalid token: {e}')

    text = sanitize_text(inp.text)
    if len(text) < 3:
        raise HTTPException(400,'Text too short')

    try:
        sentiment = await post_json(f'{SENTIMENT_URL}/analyze', {'text': text})
    except Exception as e:
        raise HTTPException(502, f'Sentiment service error: {e}')

    try:
        urgency = await post_json(f'{URGENCY_URL}/detect', {'text': text})
    except Exception as e:
        raise HTTPException(502, f'Urgency service error: {e}')

    try:
        themes = await post_json(f'{NLP_URL}/themes', {'text': text})
    except Exception as e:
        raise HTTPException(502, f'NLP service error: {e}')

    try:
        evidence = await post_json(f'{IR_URL}/search', {'query': themes.get('summary', text), 'k': 5})
    except Exception as e:
        raise HTTPException(502, f'IR service error: {e}')

    try:
        suggestion = await post_json(
            f'{SUGGESTION_URL}/suggest',
            {'feedback': text, 'themes': themes.get('summary',''), 'entities': themes.get('entities', [])}
        )
    except Exception as e:
        raise HTTPException(502, f'Suggestion service error: {e}')

    return {'sentiment': sentiment, 'urgency': urgency, 'themes': themes, 'evidence': evidence, 'suggestion': suggestion}
