from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt, os, time
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from fastapi.middleware.cors import CORSMiddleware

load_dotenv = lambda: None
try:
    from dotenv import load_dotenv as _ld
    _ld()
except Exception:
    pass

JWT_SECRET = os.getenv('JWT_SECRET', 'change_me_secret')
ALGO = 'HS256'
FERNET_KEY = os.getenv('FERNET_KEY')
if FERNET_KEY is None:
    FERNET_KEY = Fernet.generate_key().decode()
try:
    fernet = Fernet(FERNET_KEY.encode())
except Exception:
    # Fallback: supplied key was invalid; generate a valid one to avoid startup crash
    FERNET_KEY = Fernet.generate_key().decode()
    fernet = Fernet(FERNET_KEY.encode())

app = FastAPI(title='Security Service')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:8080", "http://localhost:8080", "http://127.0.0.1:3000", "http://localhost:3000", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

auth_scheme = HTTPBearer()

class LoginIn(BaseModel):
    username: str
    password: str
    role: str = 'employee'  # Default role

@app.post('/login')
def login(payload: LoginIn):
    # Demo credentials - in real app, check against database
    valid_credentials = {
        'admin': {'password': 'admin123', 'role': 'admin', 'name': 'HR Admin'},
        'employee': {'password': 'employee123', 'role': 'employee', 'name': 'John Employee'},
        'admin@company.com': {'password': 'admin123', 'role': 'admin', 'name': 'HR Admin'},
        'employee@company.com': {'password': 'employee123', 'role': 'employee', 'name': 'John Employee'}
    }
    
    user_info = valid_credentials.get(payload.username)
    if user_info and user_info['password'] == payload.password:
        # Override role if provided in request
        role = payload.role if payload.role in ['admin', 'employee'] else user_info['role']
        
        token = jwt.encode({
            'sub': payload.username, 
            'role': role,
            'name': user_info['name'],
            'exp': int(time.time()) + 3600
        }, JWT_SECRET, algorithm=ALGO)
        
        return {
            'access_token': token,
            'user': {
                'username': payload.username,
                'role': role,
                'name': user_info['name']
            }
        }
    raise HTTPException(401, 'invalid credentials')

@app.get('/verify')
def verify_token(creds: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        data = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[ALGO])
        return {
            'ok': True, 
            'sub': data['sub'],
            'role': data.get('role', 'employee'),
            'name': data.get('name', 'Unknown User')
        }
    except Exception as e:
        raise HTTPException(401, str(e))

@app.get('/user-info')
def get_user_info(creds: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        data = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[ALGO])
        return {
            'username': data['sub'],
            'role': data.get('role', 'employee'),
            'name': data.get('name', 'Unknown User')
        }
    except Exception as e:
        raise HTTPException(401, str(e))

@app.post('/encrypt')
def encrypt_text(text: str):
    return {'cipher': fernet.encrypt(text.encode()).decode()}

@app.post('/decrypt')
def decrypt_text(cipher: str):
    return {'plain': fernet.decrypt(cipher.encode()).decode()}
