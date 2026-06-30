from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .agent import evaluate_candidate
import traceback

app = FastAPI(title = "HR Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

class EvaluationRequest(BaseModel):
    filename: str

@app.post("/api/evaluate")
async def evaluate(request: EvaluationRequest):
    try:
        html_output = await evaluate_candidate(request.filename)
        return {"status": "success", "html": html_output}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code = 500, detail=str(e))