"""Build a portable NumPy cosine-search index from supplied DIEMS data."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from backend.utils.config import (DATA_DIR, EMBEDDING_MODEL, INDEX_METADATA_PATH,
                                  INDEX_VECTORS_PATH, KNOWLEDGE_BASE_PATH, USE_LOCAL_SENTENCE_MODEL, VECTOR_STORE_DIR)

FALLBACK_DIMENSIONS = 2048


def record(text, source, category="General", record_id=None):
    return {"id": record_id or hashlib.sha1(text.encode("utf-8")).hexdigest()[:16],
            "text": text.strip(), "metadata": {"source": source, "category": category}}


def load_jsonl(path: Path):
    records = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path.name} line {number}: {exc.msg}") from exc
            if not isinstance(item, dict) or not item.get("text"):
                raise ValueError(f"Invalid record at {path.name} line {number}: text is required")
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            records.append(record(str(item["text"]), str(metadata.get("source", path.name)),
                                  str(metadata.get("category", "General")), str(item.get("id", number))))
    return records


def load_csv(path: Path):
    records = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            row = {key: (value or "").strip() for key, value in row.items()}
            if not any(row.values()):
                continue
            source, category = row.get("source") or path.name, row.get("category") or row.get("topic") or path.stem
            if row.get("question") and row.get("answer"):
                text = f"Question: {row['question']}\nAnswer: {row['answer']}"
            elif row.get("topic") and row.get("details"):
                text = f"Topic: {row['topic']}\nDetails: {row['details']}"
            else:
                text = "\n".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in row.items() if value)
            records.append(record(text, source, category))
    return records


def load_excel(path: Path):
    try:
        import openpyxl
    except ImportError:
        return []
    book, records = openpyxl.load_workbook(path, read_only=True, data_only=True), []
    for sheet in book.worksheets:
        rows = sheet.iter_rows(values_only=True)
        headers = [str(value).strip() if value is not None else "" for value in next(rows, ())]
        for values in rows:
            row = {headers[i]: str(value).strip() for i, value in enumerate(values)
                   if i < len(headers) and headers[i] and value is not None}
            if row:
                records.append(record("\n".join(f"{key}: {value}" for key, value in row.items()),
                                      f"{path.name} / {sheet.title}", sheet.title))
    book.close()
    return records


def load_documents():
    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError(f"Knowledge-base file not found: {KNOWLEDGE_BASE_PATH}")
    records = load_jsonl(KNOWLEDGE_BASE_PATH)
    for path in sorted(DATA_DIR.glob("*.csv")):
        records.extend(load_csv(path))
    for path in sorted(DATA_DIR.glob("*.xlsx")):
        records.extend(load_excel(path))
    return records


def lexical_vectors(texts):
    vectors = np.zeros((len(texts), FALLBACK_DIMENSIONS), dtype=np.float32)
    for row, text in enumerate(texts):
        for token in text.lower().split():
            vectors[row, int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % FALLBACK_DIMENSIONS] += 1
    return vectors


def normalize(vectors):
    return vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)


def embed_texts(texts):
    if not USE_LOCAL_SENTENCE_MODEL:
        print("Using lexical NumPy fallback (set USE_LOCAL_SENTENCE_MODEL=true after caching the embedding model to enable Sentence Transformers).")
        return lexical_vectors(texts), "lexical-numpy"
    try:
        from sentence_transformers import SentenceTransformer
        # Do not make startup/ingestion hang on a network download. A locally
        # cached model is used when present; otherwise NumPy fallback is chosen.
        model = SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
        return model.encode(texts, convert_to_numpy=True, show_progress_bar=False).astype(np.float32), "sentence-transformers"
    except Exception as exc:
        print(f"Sentence Transformer unavailable ({exc.__class__.__name__}); using lexical NumPy fallback.")
        return lexical_vectors(texts), "lexical-numpy"


def build_index():
    records = load_documents()
    vectors, embedding_type = embed_texts([item["text"] for item in records])
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(INDEX_VECTORS_PATH, normalize(vectors))
    INDEX_METADATA_PATH.write_text(json.dumps({"records": records, "embedding_type": embedding_type,
                                                "embedding_model": EMBEDDING_MODEL}, ensure_ascii=False), encoding="utf-8")
    print(f"Indexed {len(records)} records using {embedding_type}.")


if __name__ == "__main__":
    build_index()
