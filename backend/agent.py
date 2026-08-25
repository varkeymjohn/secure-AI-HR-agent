import asyncio
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from .prompts import SYSTEM_PROMPT, USER_PROMPT
from .rag_engine import vulnerable_global_search, secure_global_search

llm = ChatOllama(model="qwen3:1.7b", temperature=0.1)

async def _evaluate_single_candidate(doc_text: str, meta: dict, distance: float, rank: int) -> dict:
    """Evaluates a single candidate chunk in strict isolation to prevent cross-contamination."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT)
    ])
    chain = prompt | llm
    response = await chain.ainvoke({"context": doc_text})
    
    return {
        "filename": meta.get("filename", "unknown.pdf"),
        "rank": rank,
        "distance": round(distance, 4),
        "status": meta.get("type", "retrieved"),
        "html": response.content
    }

async def run_screening_attack(query: str) -> dict:
    retrieval_data = vulnerable_global_search(query)
    
    # Evaluate each retrieved candidate independently
    tasks = [
        _evaluate_single_candidate(
            doc_text=item["doc_full"],
            meta=item["meta"],
            distance=item["distance"],
            rank=idx + 1
        )
        for idx, item in enumerate(retrieval_data["matches"])
    ]
    
    evaluations = await asyncio.gather(*tasks)
    return {"evaluations": evaluations}

async def run_screening_defense(query: str) -> dict:
    retrieval_data = secure_global_search(query)
    
    tasks = [
        _evaluate_single_candidate(
            doc_text=item["doc_full"],
            meta=item["meta"],
            distance=item["distance"],
            rank=idx + 1
        )
        for idx, item in enumerate(retrieval_data["matches"])
    ]
    
    evaluations = await asyncio.gather(*tasks)
    return {"evaluations": evaluations}