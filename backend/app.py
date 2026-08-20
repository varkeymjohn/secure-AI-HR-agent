import os
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .hr_db import hr_database
from .vulnerable_agent import process_vulnerable
from .secure_agent import process_secure

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/api/db")
async def get_db():
    return hr_database

@app.post("/api/upload/vulnerable")
async def upload_vulnerable(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    result = await process_vulnerable(file_path)
    return {"status": "success", "message": result}

@app.post("/api/upload/secure")
async def upload_secure(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    result = await process_secure(file_path)
    return {"status": "success", "message": result}