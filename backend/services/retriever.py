
import json
import re
import numpy as np

from backend.services.ingest import lexical_vectors, normalize
from backend.utils.config import INDEX_METADATA_PATH, INDEX_VECTORS_PATH, TOP_K

STOP_WORDS = {"a", "an", "the", "is", "are", "do", "does", "what", "which", "where", "how", "for", "of", "to", "in", "on", "and", "or", "about", "at", "with", "when", "i", "my", "me", "available"}


def tokens(text):
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS}


class DIEMSRetriever:
    def __init__(self):
        self.records, self.vectors, self.embedding_type, self.model, self.error = [], None, None, None, None
        self.reload()

    @property
    def ready(self): return self.vectors is not None and bool(self.records)

    @property
    def record_count(self): return len(self.records)

    def reload(self):
        if not INDEX_METADATA_PATH.exists() or not INDEX_VECTORS_PATH.exists():
            self.error = "Knowledge index is missing. Run: venv\\Scripts\\python -m backend.services.ingest"
            return
        try:
            metadata = json.loads(INDEX_METADATA_PATH.read_text(encoding="utf-8"))
            self.records, self.embedding_type = metadata["records"], metadata["embedding_type"]
            self.vectors = np.load(INDEX_VECTORS_PATH)
            if self.vectors.ndim != 2 or len(self.vectors) != len(self.records): raise ValueError("metadata and vector counts do not match")
            if self.embedding_type == "sentence-transformers":
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(metadata["embedding_model"])
        except Exception as exc:
            self.records, self.vectors = [], None
            self.error = f"Knowledge index is corrupt or incompatible ({exc}). Rebuild it with: venv\\Scripts\\python -m backend.services.ingest"

    def search(self, query, limit=TOP_K):
        if not self.ready or not query.strip(): return []
        if self.embedding_type == "lexical-numpy":
            query_words = tokens(query)
            ranked = []
            for index, item in enumerate(self.records):
                question, _, answer = item["text"].partition("\nAnswer:")
                question_words, answer_words = tokens(question), tokens(answer)
                score = (2 * len(query_words & question_words) + 0.2 * len(query_words & answer_words)) / max(2 * len(query_words), 1)
                if score >= 0.20:
                    ranked.append((score, index))
            # Keep earlier records first on ties: the curated JSONL is loaded
            # before supplemental CSV/XLSX material and is the authority.
            return [{**self.records[index], "score": round(float(score), 3)}
                    for score, index in sorted(ranked, key=lambda item: (-item[0], item[1]))[:limit]]
        vector = (self.model.encode([query], convert_to_numpy=True).astype(np.float32)
                  if self.embedding_type == "sentence-transformers" else lexical_vectors([query]))
        scores = self.vectors @ normalize(vector)[0]
        results = []
        for index in np.argsort(scores)[::-1][:limit]:
            if scores[index] > 0.08:
                results.append({**self.records[int(index)], "score": round(float(scores[index]), 3)})
        return results


retriever = DIEMSRetriever()
