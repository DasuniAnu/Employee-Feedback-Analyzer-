# Sentiment Agent with Hugging Face

This service provides sentiment analysis using Hugging Face's pre-trained models instead of OpenAI.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Hugging Face Token:**
   ```bash
   python setup_hf.py
   ```
   This will automatically configure your Hugging Face token in the `.env` file.

3. **Start the Service:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Usage

### API Endpoint

**POST** `/analyze`

**Request Body:**
```json
{
  "text": "Your text to analyze"
}
```

**Response:**
```json
{
  "label": "Positive|Negative|Neutral",
  "score": 0.95
}
```

### Example Usage

```python
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={"text": "I love this product!"}
)

result = response.json()
print(f"Sentiment: {result['label']}")
print(f"Confidence: {result['score']}")
```

## Testing

Run the test script to verify the service is working:

```bash
python test_sentiment.py
```

## Model Details

- **Model:** `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Task:** Sentiment Analysis
- **Labels:** Positive, Negative, Neutral
- **Framework:** Hugging Face Transformers

## Fallback

If the Hugging Face model fails to load, the service falls back to a simple heuristic-based sentiment analysis using keyword matching.

## Environment Variables

- `HUGGINGFACE_TOKEN`: Your Hugging Face API token (automatically set by setup script)
