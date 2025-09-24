from fastapi import FastAPI
from transformers import pipeline

# Initialize FastAPI app
app = FastAPI(title="Sentiment Detector Agent")

# Load HuggingFace sentiment model
sentiment_model = pipeline("sentiment-analysis")

@app.get("/")
def home():
    return {"message": "Sentiment Detector Agent is running"}

@app.post("/analyze/")
def analyze_feedback(feedback: str):
    result = sentiment_model(feedback)[0]
    return {
        "feedback": feedback,
        "sentiment": result['label'],
        "score": float(result['score'])
    }
