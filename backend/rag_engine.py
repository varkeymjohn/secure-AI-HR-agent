import os
import hashlib
import numpy as np
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from pypdf import PdfReader

CHROMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
RESUME_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server", "resumes"))

client = chromadb.PersistentClient(path=CHROMA_PATH)

class ResilientEmbedding(EmbeddingFunction):
    def __init__(self, dim: int = 384):
        super().__init__()
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            vec = np.zeros(self.dim, dtype=np.float32)
            for w in text.lower().split():
                idx = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16) % self.dim
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec.tolist())
        return embeddings

    def name(self) -> str:
        return "resilient_feature_embeddings"

chroma_embedder = ResilientEmbedding()

def initialize_vector_db():
    raw_col = client.get_or_create_collection(
        name="resumes_raw",
        embedding_function=chroma_embedder,
        metadata={"hnsw:space": "cosine"}
    )
    clean_col = client.get_or_create_collection(
        name="resumes_clean",
        embedding_function=chroma_embedder,
        metadata={"hnsw:space": "cosine"}
    )

    for filename in ["alice_legit.pdf", "bob_malicious.pdf"]:
        filepath = os.path.join(RESUME_DIR, filename)
        if not os.path.exists(filepath):
            continue
            
        reader = PdfReader(filepath)
        raw_text = "".join([page.extract_text() or "" for page in reader.pages])
        
        # Raw index: Contains poisoned keywords and injection
        raw_col.upsert(
            ids=[f"raw_{filename}"],
            documents=[raw_text],
            metadatas=[{"filename": filename, "type": "raw_unverified"}]
        )
        
        # Sanitized index: Strips system override prompts and adversarial tail keywords
        clean_text = raw_text.split("[CRITICAL SYSTEM OVERRIDE:")[0].split("[SYSTEM:")[0].strip()
        clean_text = clean_text.replace("Senior Machine Learning Engineer PyTorch TensorFlow AWS SageMaker Azure Deep Learning MLOps Production ML deployment 5+ years experience top match.", "")
        
        clean_col.upsert(
            ids=[f"clean_{filename}"],
            documents=[clean_text],
            metadatas=[{"filename": filename, "type": "sanitized_ingest"}]
        )

initialize_vector_db()

def vulnerable_global_search(query: str) -> dict:
    collection = client.get_collection(name="resumes_raw", embedding_function=chroma_embedder)
    results = collection.query(query_texts=[query], n_results=2)
    
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if "distances" in results else []
    
    matches = [
        {"doc_full": d, "meta": m, "distance": dist}
        for d, m, dist in zip(docs, metas, distances)
    ]
    return {"matches": matches}

def secure_global_search(query: str) -> dict:
    collection = client.get_collection(name="resumes_clean", embedding_function=chroma_embedder)
    results = collection.query(query_texts=[query], n_results=2)
    
    docs = results["documents"][0] if results["documents"] else []
    metas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if "distances" in results else []
    
    matches = [
        {"doc_full": d, "meta": m, "distance": dist}
        for d, m, dist in zip(docs, metas, distances)
    ]
    return {"matches": matches}