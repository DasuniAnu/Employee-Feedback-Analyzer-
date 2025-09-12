from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware