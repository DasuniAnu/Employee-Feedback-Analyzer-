from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title='Feedback Storage Service')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:8080", "http://localhost:8080", "http://127.0.0.1:3000", "http://localhost:3000", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Simple file-based storage (in production, use a database)
STORAGE_FILE = "feedback_data.json"

class FeedbackSubmission(BaseModel):
    text: str
    employee_email: str
    employee_name: str
    rating: Optional[int] = None
    timestamp: Optional[str] = None

class FeedbackAnalysis(BaseModel):
    sentiment: dict
    urgency: dict
    themes: dict
    evidence: dict
    suggestion: dict

class StoredFeedback(BaseModel):
    id: int
    text: str
    employee_email: str
    employee_name: str
    rating: Optional[int]
    timestamp: str
    analysis: FeedbackAnalysis
    status: str = "pending"  # pending, resolved, in_progress
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

def load_feedback_data():
    """Load feedback data from file"""
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_feedback_data(data):
    """Save feedback data to file"""
    try:
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving feedback data: {e}")
        return False

@app.post('/submit')
async def submit_feedback(feedback: FeedbackSubmission, analysis: FeedbackAnalysis):
    """Store feedback with analysis results"""
    try:
        # Load existing data
        data = load_feedback_data()
        
        # Generate new ID
        new_id = max([f.get('id', 0) for f in data], default=0) + 1
        
        # Create stored feedback object
        stored_feedback = StoredFeedback(
            id=new_id,
            text=feedback.text,
            employee_email=feedback.employee_email,
            employee_name=feedback.employee_name,
            rating=feedback.rating,
            timestamp=feedback.timestamp or datetime.now().isoformat(),
            analysis=analysis,
            status="pending"
        )
        
        # Add to data
        data.append(stored_feedback.dict())
        
        # Save to file
        if save_feedback_data(data):
            return {"success": True, "id": new_id, "message": "Feedback stored successfully"}
        else:
            raise HTTPException(500, "Failed to save feedback")
            
    except Exception as e:
        raise HTTPException(500, f"Error storing feedback: {str(e)}")

@app.get('/feedback')
async def get_all_feedback():
    """Get all stored feedback"""
    try:
        data = load_feedback_data()
        return {"feedback": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(500, f"Error loading feedback: {str(e)}")

@app.get('/feedback/{feedback_id}')
async def get_feedback_by_id(feedback_id: int):
    """Get specific feedback by ID"""
    try:
        data = load_feedback_data()
        feedback = next((f for f in data if f.get('id') == feedback_id), None)
        
        if not feedback:
            raise HTTPException(404, "Feedback not found")
            
        return feedback
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error loading feedback: {str(e)}")

@app.put('/feedback/{feedback_id}/status')
async def update_feedback_status(feedback_id: int, status: str, assigned_to: Optional[str] = None, notes: Optional[str] = None):
    """Update feedback status and assignment"""
    try:
        data = load_feedback_data()
        feedback = next((f for f in data if f.get('id') == feedback_id), None)
        
        if not feedback:
            raise HTTPException(404, "Feedback not found")
        
        # Update fields
        feedback['status'] = status
        if assigned_to:
            feedback['assigned_to'] = assigned_to
        if notes:
            feedback['notes'] = notes
        
        # Save updated data
        if save_feedback_data(data):
            return {"success": True, "message": "Feedback updated successfully"}
        else:
            raise HTTPException(500, "Failed to update feedback")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error updating feedback: {str(e)}")

@app.delete('/feedback/{feedback_id}')
async def delete_feedback(feedback_id: int):
    """Delete feedback by ID"""
    try:
        data = load_feedback_data()
        original_count = len(data)
        
        # Remove feedback with matching ID
        data = [f for f in data if f.get('id') != feedback_id]
        
        if len(data) == original_count:
            raise HTTPException(404, "Feedback not found")
        
        # Save updated data
        if save_feedback_data(data):
            return {"success": True, "message": "Feedback deleted successfully"}
        else:
            raise HTTPException(500, "Failed to delete feedback")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error deleting feedback: {str(e)}")

@app.get('/stats')
async def get_feedback_stats():
    """Get feedback statistics"""
    try:
        data = load_feedback_data()
        
        if not data:
            return {
                "total": 0,
                "by_sentiment": {"Positive": 0, "Negative": 0, "Neutral": 0},
                "by_urgency": {"High": 0, "Medium": 0, "Low": 0},
                "by_status": {"pending": 0, "resolved": 0, "in_progress": 0}
            }
        
        # Calculate statistics
        stats = {
            "total": len(data),
            "by_sentiment": {"Positive": 0, "Negative": 0, "Neutral": 0},
            "by_urgency": {"High": 0, "Medium": 0, "Low": 0},
            "by_status": {"pending": 0, "resolved": 0, "in_progress": 0}
        }
        
        for feedback in data:
            # Sentiment stats
            sentiment = feedback.get('analysis', {}).get('sentiment', {}).get('label', 'Neutral')
            if sentiment in stats["by_sentiment"]:
                stats["by_sentiment"][sentiment] += 1
            
            # Urgency stats
            urgency = feedback.get('analysis', {}).get('urgency', {}).get('urgency', 'Low')
            if urgency in stats["by_urgency"]:
                stats["by_urgency"][urgency] += 1
            
            # Status stats
            status = feedback.get('status', 'pending')
            if status in stats["by_status"]:
                stats["by_status"][status] += 1
        
        return stats
        
    except Exception as e:
        raise HTTPException(500, f"Error calculating stats: {str(e)}")

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "feedback-storage"}
