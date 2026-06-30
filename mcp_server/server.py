import os
from mcp.server.fastmcp import FastMCP
from pypdf import PdfReader

mcp = FastMCP("Resume Server")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESUME_DIR = os.path.join(BASE_DIR, "resumes")

@mcp.resource("resume://{filename}")
def get_resume(filename: str) -> str:
    file_path = os.path.join(RESUME_DIR, os.path.basename(filename))

    if not os.path.exists(file_path):
        raise ValueError(f"Resume not found: {filename}!")

    if not os.path.basename(filename).lower().endswith(".pdf"):
        raise ValueError("This resource supports only PDF files.")

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text

    except Exception as e:
        return f"Error reading PDF: {str(e)}"
    
if __name__ == "__main__":
    mcp.run()