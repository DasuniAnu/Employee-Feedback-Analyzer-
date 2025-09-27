import os, json
from dotenv import load_dotenv
try:
    from openai import OpenAI
    from openai import RateLimitError
except Exception:
    OpenAI = None
    RateLimitError = Exception

load_dotenv = lambda: None
try:
    from dotenv import load_dotenv as _ld
    _ld()
except Exception:
    pass

client = None
if OpenAI is not None and os.getenv('OPENAI_API_KEY'):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
INDEX_PATH = os.path.join(os.path.dirname(__file__), 'index.json')
EMB_PATH = os.path.join(os.path.dirname(__file__), 'emb.npy')

os.makedirs(DATA_DIR, exist_ok=True)

corpus = []
for fname in os.listdir(DATA_DIR):
    path = os.path.join(DATA_DIR, fname)
    if not os.path.isfile(path):
        continue
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    corpus.append({'doc_id': fname, 'title': fname, 'text': text[:4000]})

# Offline mode if no client or explicitly requested
OFFLINE = client is None or os.getenv('IR_OFFLINE', '').strip() == '1'

if OFFLINE:
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, ensure_ascii=False)
    import numpy as np
    np.save(EMB_PATH, np.zeros((len(corpus), 384), dtype='float32'))
    print('Built fallback index (offline mode) for', len(corpus))
else:
    try:
        embs = []
        for doc in corpus:
            resp = client.embeddings.create(model='text-embedding-3-small', input=doc['text'])
            embs.append(resp.data[0].embedding)
        import numpy as np
        np.save(EMB_PATH, np.array(embs, dtype='float32'))
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump(corpus, f, ensure_ascii=False)
        print('Indexed', len(corpus))
    except (RateLimitError, Exception) as e:
        # Fallback on any API failure (e.g., quota exceeded)
        print('Embedding build failed, falling back to offline index:', str(e))
        import numpy as np
        np.save(EMB_PATH, np.zeros((len(corpus), 384), dtype='float32'))
        with open(INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump(corpus, f, ensure_ascii=False)
        print('Built fallback index for', len(corpus))
