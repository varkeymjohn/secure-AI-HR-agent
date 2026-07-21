# HR Screener Application (with Prompt Injection Demo)

This repository contains a proof-of-concept HR Screener application powered by LLMs. It demonstrates how to integrate a FastAPI backend with LangChain, local LLMs (via Ollama), and the Model Context Protocol (MCP) to analyze PDF resumes. 

**Note:** This application intentionally includes an **Insecure Output Handling vulnerability** (XSS via Prompt Injection) for educational and security demonstration purposes.

## Architecture

The application is split into several interconnected components:

1. **Frontend (`index.html`)**: A simple web dashboard that allows users to select a resume and view the LLM's evaluation. It is intentionally vulnerable to Cross-Site Scripting (XSS) by directly rendering raw HTML received from the backend using `innerHTML`.
2. **Backend API (`app.py`)**: A FastAPI server that exposes an endpoint (`/api/evaluate`) for the frontend to request candidate evaluations.
3. **AI Agent (`agent.py` & `prompts.py`)**: Uses `langchain_ollama` and an MCP client to retrieve resumes, format prompts, and evaluate the candidate using the `qwen3:1.7b` local model.
4. **MCP Server (`server.py`)**: A Model Context Protocol (MCP) server built with `FastMCP` that securely reads and extracts text from local PDF resumes in the `resumes/` directory.

## Prerequisites

- **Python 3.8+**
- **Ollama**: Must be installed and running locally.
- **Model**: Pull the required Qwen model before running:
  ```bash
  ollama pull qwen3:1.7b
  ```

## Installation

1. Clone the repository and navigate to the project directory.
2. Install the required Python dependencies:
   ```bash
   pip install fastapi uvicorn pydantic langchain_ollama langchain_core mcp pypdf python-dotenv
   ```
3. Ensure you have a `resumes` folder in the same directory as `server.py` containing PDF resumes (e.g., `alice_legit.pdf` and `bob_malicious.pdf`).

## Running the Application

**1. Start the FastAPI Backend**
Run the FastAPI application using Uvicorn (make sure you are in the directory containing `app.py`):
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```
*(Note: The MCP Server runs automatically as a subprocess via the `agent.py` client.)*

**2. Start the Frontend**
Open `index.html` directly in your browser, or serve it using a simple HTTP server:
```bash
python -m http.server 8080
```
Then navigate to `http://localhost:8080` in your web browser.

## Security Demonstration (The Vulnerability)

This application serves as a demonstration of **Prompt Injection leading to XSS (Cross-Site Scripting)**. 

- The LLM is instructed to return *raw HTML*.
- A malicious candidate can craft a resume (e.g., `bob_malicious.pdf`) with hidden text designed to hijack the LLM's instructions (Prompt Injection), forcing it to output a malicious `<script>` payload instead of standard evaluation HTML.
- Because `index.html` takes the LLM's output and directly injects it into the DOM (`resultsDiv.innerHTML = data.html;`), the injected JavaScript will execute in the recruiter's browser.

**Mitigation:** In a production environment, LLM outputs should never be trusted as safe HTML. Always use text-based rendering (like Markdown), or properly sanitize/escape HTML outputs before rendering them in the DOM (e.g., using DOMPurify).