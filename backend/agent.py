import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from .prompts import (
    SYSTEM_PROMPT_SANITIZER, USER_PROMPT_SANITIZER,
    SYSTEM_PROMPT_EVALUATOR, USER_PROMPT_EVALUATOR
)
import httpx

load_dotenv()

async def get_resume_text(filename: str) -> str:
    # Simulating a call to the FastMCP server's resource endpoint
    # In a real environment, you would use the official MCP client SDK here.
    async with httpx.AsyncClient() as client:
        # Assuming the FastMCP server exposes an HTTP bridge or you fetch via its transport layer
        # For demonstration, we simply wrap the file reading logic here:
        from pypdf import PdfReader
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resumes", os.path.basename(filename))
        
        if not os.path.exists(file_path):
            raise ValueError(f"Resume not found: {filename}!")
            
        reader = PdfReader(file_path)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text

async def evaluate_candidate(filename: str) -> str:
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # 1. Fetch the raw, untrusted text from the PDF
    raw_text = await get_resume_text(filename)
    
    # 2. Defense Layer: Unprivileged Sanitizer Model
    # Forces raw text into a strict JSON structure, destroying prompt injections.
    sanitizer_response = await client.chat.completions.create(
        model="gpt-3.5-turbo", # Can use a smaller, restricted model here
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_SANITIZER},
            {"role": "user", "content": USER_PROMPT_SANITIZER.format(resume_text=raw_text)}
        ]
    )
    
    sanitized_data = sanitizer_response.choices[0].message.content
    
    # 3. Decision Layer: Privileged Evaluator Model
    # Assesses the candidate using only the safe, sanitized JSON.
    evaluator_response = await client.chat.completions.create(
        model="gpt-4", # Main decision making model
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_EVALUATOR},
            {"role": "user", "content": USER_PROMPT_EVALUATOR.format(sanitized_json=sanitized_data)}
        ]
    )
    
    return evaluator_response.choices[0].message.content