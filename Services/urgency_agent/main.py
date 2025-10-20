from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import google.generativeai as genai
except Exception:
    genai = None

load_dotenv = lambda: None
try:
    from dotenv import load_dotenv as _ld
    _ld()
except Exception:
    pass

# Configure Gemini API
gemini_api_key = os.getenv('GOOGLE_API_KEY') or 'AIzaSyC2vCvUu3PL6KtVwWA4ZSaFYf283VMSFUs'
gemini_model = None
if genai is not None and gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ Gemini urgency model loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load Gemini model: {e}")
        gemini_model = None

app = FastAPI(title='Urgency Agent (Gemini Only)')

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
        return {
            'urgency': 'High', 
            'confidence': min(0.9, 0.6 + (high_count * 0.1)), 
            'reason': f'Contains {high_count} high-urgency keywords',
            'model_used': 'Rule-based'
        }
    elif medium_count > 0:
        return {
            'urgency': 'Medium', 
            'confidence': min(0.8, 0.5 + (medium_count * 0.1)), 
            'reason': f'Contains {medium_count} medium-urgency keywords',
            'model_used': 'Rule-based'
        }
    else:
        return {
            'urgency': 'Low', 
            'confidence': 0.7, 
            'reason': 'No urgency indicators detected',
            'model_used': 'Rule-based'
        }

@app.post('/detect')
async def detect_urgency(inp: Inp):
    text = (inp.text or '').strip()
    if not text:
        return {'urgency': 'Low', 'confidence': 1.0, 'reason': 'Empty input', 'model_used': 'Rule-based'}

    # Try Gemini first
    if gemini_model is not None:
        try:
            prompt = f"""
            Analyze the urgency level of the following employee feedback.
            
            Classify it as:
            - High urgency: requires immediate HR attention (harassment, discrimination, threats, legal issues, mental health crises)
            - Medium urgency: needs prompt follow-up (conflicts, stress, complaints, concerns)
            - Low urgency: routine feedback (general comments, suggestions, normal workplace issues)
            
            Return ONLY a JSON object with:
            - "urgency": "High", "Medium", or "Low"
            - "confidence": number between 0.0 and 1.0
            - "reason": brief explanation
            
            Feedback: "{text}"
            
            JSON format:
            {{"urgency": "Medium", "confidence": 0.75, "reason": "Contains stress-related concerns"}}
            """
            
            response = gemini_model.generate_content(prompt)
            text_response = (response.text or '').strip()
            
            import json
            try:
                # Try to parse as JSON
                data = json.loads(text_response)
            except Exception:
                # Try to extract JSON from the response
                import re
                match = re.search(r'\{[^}]*\}', text_response)
                if match:
                    data = json.loads(match.group(0))
                else:
                    raise Exception("No valid JSON found")
            
            # Validate the response
            if isinstance(data, dict) and 'urgency' in data:
                urgency = data['urgency']
                confidence = float(data.get('confidence', 0.5))
                reason = data.get('reason', 'Analyzed by Gemini')
                
                # Ensure valid values
                if urgency not in ['High', 'Medium', 'Low']:
                    urgency = 'Low'
                if not 0.0 <= confidence <= 1.0:
                    confidence = 0.5
                    
                return {
                    'urgency': urgency,
                    'confidence': confidence,
                    'reason': reason,
                    'model_used': 'Gemini'
                }
            else:
                raise Exception("Invalid response format")
                
        except Exception as e:
            print(f"Gemini urgency analysis error: {e}")
            # Fall back to heuristic
            return heuristic_urgency(text)
    
    # Fallback to heuristic if Gemini is not available
    return heuristic_urgency(text)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)