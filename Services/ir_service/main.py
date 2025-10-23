from fastapi import FastAPI
from pydantic import BaseModel
import json, os
import numpy as np
from dotenv import load_dotenv
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv = lambda: None
try:
    from dotenv import load_dotenv as _ld
    _ld()
except Exception:
    pass

client = None
if OpenAI is not None and os.getenv('OPENAI_API_KEY'):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

BASE = os.path.dirname(__file__)
INDEX_PATH = os.path.join(BASE, 'index.json')
EMB_PATH = os.path.join(BASE, 'emb.npy')

if os.path.exists(INDEX_PATH):
    INDEX = json.load(open(INDEX_PATH, 'r', encoding='utf-8'))
else:
    INDEX = []

if os.path.exists(EMB_PATH):
    try:
        EMB = np.load(EMB_PATH)
    except Exception:
        EMB = np.zeros((len(INDEX), 384), dtype='float32')
else:
    EMB = np.zeros((len(INDEX), 384), dtype='float32')

app = FastAPI(title='IR Service (OpenAI embeddings)')

class Inp(BaseModel):
    query: str
    k: int = 5

@app.post('/search')
async def search(inp: Inp):
    # Build query vector with fallback
    try:
        if client is not None:
            q = client.embeddings.create(model='text-embedding-3-small', input=inp.query)
            qv = np.array(q.data[0].embedding, dtype='float32')
        else:
            qv = np.zeros((EMB.shape[1],), dtype='float32')
    except Exception:
        qv = np.zeros((EMB.shape[1],), dtype='float32')

    if EMB.size == 0 or len(INDEX) == 0 or EMB.shape[0] != len(INDEX):
        return {'query': inp.query, 'results': []}

    try:
        denom = (np.linalg.norm(EMB, axis=1) * (np.linalg.norm(qv) + 1e-10) + 1e-10)
        sims = (EMB @ qv) / denom
        if sims.size == 0:
            return {'query': inp.query, 'results': []}
        k = max(0, min(int(inp.k), len(INDEX)))
        if k == 0:
            return {'query': inp.query, 'results': []}
        topk = sims.argsort()[-k:][::-1]
        results = []
        for i in topk:
            d = INDEX[int(i)]
            results.append({'doc_id': d.get('doc_id', str(i)), 'title': d.get('title',''), 'snippet': d.get('text','')[:300], 'score': float(sims[i])})
        return {'query': inp.query, 'results': results}
    except Exception:
        return {'query': inp.query, 'results': []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
