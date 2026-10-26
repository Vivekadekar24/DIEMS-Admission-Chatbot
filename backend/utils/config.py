
"""Central, path-safe configuration for the DIEMS chatbot."""
from pathlib import Path
import os
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
DATA_DIR = PROJECT_ROOT / "data" / "documents"
KNOWLEDGE_BASE_PATH = DATA_DIR / "diems_rag_knowledge_base.jsonl"
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_store"
INDEX_METADATA_PATH = VECTOR_STORE_DIR / "index.json"
INDEX_VECTORS_PATH = VECTOR_STORE_DIR / "vectors.npy"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
TOP_K = max(1, int(os.getenv("TOP_K", "4")))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
# Set this only after pre-downloading the model into the local Hugging Face cache.
USE_LOCAL_SENTENCE_MODEL = os.getenv("USE_LOCAL_SENTENCE_MODEL", "false").lower() == "true"
LLM_API_URL = os.getenv("LLM_API_URL", "").strip()
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "").strip()
