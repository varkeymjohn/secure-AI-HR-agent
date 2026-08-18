import json
import os
from dotenv import load_dotenv
import httpx
from openai import AsyncOpenAI
from pypdf import PdfReader
from .prompts import (
    SYSTEM_PROMPT_EVALUATOR,
    SYSTEM_PROMPT_SANITIZER,
    USER_PROMPT_EVALUATOR,
    USER_PROMPT_SANITIZER,
)

load_dotenv()


async def get_resume_text(filename: str) -> str:
  # Navigate from backend/ up to the root, then into mcp_server/resumes/
  file_path = os.path.abspath(
      os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          "..",
          "mcp_server",
          "resumes",
          os.path.basename(filename),
      )
  )

  if not os.path.exists(file_path):
    raise ValueError(f"Resume not found: {filename}! Checked path: {file_path}")

  reader = PdfReader(file_path)
  text = "\n".join(
      [page.extract_text() for page in reader.pages if page.extract_text()]
  )
  return text


async def evaluate_candidate(filename: str) -> str:
  client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

  # 1. Fetch raw text from the correct folder
  raw_text = await get_resume_text(filename)

  # 2. Defense Layer: Unprivileged Sanitizer Model
  sanitizer_response = await client.chat.completions.create(
      model="gpt-3.5-turbo",
      response_format={"type": "json_object"},
      messages=[
          {"role": "system", "content": SYSTEM_PROMPT_SANITIZER},
          {
              "role": "user",
              "content": USER_PROMPT_SANITIZER.format(resume_text=raw_text),
          },
      ],
  )

  sanitized_data = sanitizer_response.choices[0].message.content

  # 3. Decision Layer: Privileged Evaluator Model
  evaluator_response = await client.chat.completions.create(
      model="gpt-4",
      messages=[
          {"role": "system", "content": SYSTEM_PROMPT_EVALUATOR},
          {
              "role": "user",
              "content": USER_PROMPT_EVALUATOR.format(
                  sanitized_json=sanitized_data
              ),
          },
      ],
  )

  return evaluator_response.choices[0].message.content