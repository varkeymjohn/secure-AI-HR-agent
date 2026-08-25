from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .agent import run_screening_attack, run_screening_defense
import traceback

# Ensure FastAPI is initialized to the variable name "app"
app = FastAPI(title="LLM09 Vector & Embedding Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScreenerRequest(BaseModel):
    query: str

@app.post("/api/screen/vulnerable")
async def screen_vulnerable(req: ScreenerRequest):
    try:
        result = await run_screening_attack(req.query)
        return {"status": "success", "mode": "vulnerable", **result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/screen/secure")
async def screen_secure(req: ScreenerRequest):
    try:
        result = await run_screening_defense(req.query)
        return {"status": "success", "mode": "secure", **result}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))