import os
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pypdf import PdfReader
from .prompts import (
    SYSTEM_PROMPT_SANITIZER,
    USER_PROMPT_SANITIZER,
    SYSTEM_PROMPT_EVALUATOR,
    USER_PROMPT_EVALUATOR,
)

load_dotenv()

# Initialize OpenAI client pointed to your local Ollama instance
client = AsyncOpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    api_key="ollama",  # Required by the SDK, ignored by local Ollama
)

# Layer-specific local models
SANITIZER_MODEL = "gemma3:270m"
EVALUATOR_MODEL = "qwen3:1.7b"


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
    # 1. Fetch the raw, untrusted text from the PDF
    raw_text = await get_resume_text(filename)

    # 2. Defense Layer: Lightweight Sanitizer Model (gemma3:270m)
    # Extracts structured JSON to isolate prompt injection
    sanitizer_response = await client.chat.completions.create(
        model=SANITIZER_MODEL,
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

    # 3. Decision Layer: Evaluator Model (qwen3:1.7b)
    # Assesses candidate using the sanitized data
    evaluator_response = await client.chat.completions.create(
        model=EVALUATOR_MODEL,
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