
from flask import Blueprint, request, jsonify
import re
from backend.services.retriever import retriever
from backend.services.llm_service import llm_service

chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/api/chat")
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Please send a JSON object with a message."}), 400
    question = data.get("message", "")

    if not isinstance(question, str) or not question.strip():
        return jsonify({
            "error": "Please enter a question."
        }), 400

    if len(question) > 1000:
        return jsonify({
            "error": "Please keep your question under 1000 characters."
        }), 400

    if not retriever.ready:
        return jsonify({"error": retriever.error or "Knowledge index is unavailable."}), 503
    try:
        results = retriever.search(question)
    except Exception:
        return jsonify({"error": "The knowledge search is temporarily unavailable. Please rebuild the index and try again."}), 503

    if not results:
        return jsonify({
            "answer": (
                "Sorry, I couldn't find a reliable answer in my "
                "current DIEMS information. Please contact the "
                "college admission office for confirmation."
            ),
            "sources": [], "category": "General", "mode": "retrieval-only"
        })

    result = results[0]
    context = "\n\n".join(item["text"] for item in results)
    fallback_answer = re.split(r"\nanswer:\s*", result["text"], maxsplit=1, flags=re.IGNORECASE)[-1]
    fallback_answer = re.split(r"\n(?:category|source):\s*", fallback_answer, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    answer = llm_service.answer(question, context) or fallback_answer
    sources = [{"source": item["metadata"].get("source", "DIEMS knowledge base"), "category": item["metadata"].get("category", "General")} for item in results]
    return jsonify({
        "answer": answer, "sources": sources, "category": result["metadata"].get("category", "General"),
        "mode": "llm" if llm_service.enabled else "retrieval-only"
    })
