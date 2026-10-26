"""Optional OpenAI-compatible LLM integration; retrieval works without it."""
import requests
from backend.utils.config import LLM_API_KEY, LLM_API_URL, LLM_MODEL


class LLMService:
    @property
    def enabled(self):
        return bool(LLM_API_URL and LLM_API_KEY and LLM_MODEL)

    def answer(self, question, context):
        if not self.enabled:
            return None
        prompt = ("Answer only from this DIEMS source context. Do not invent facts. "
                  "If the answer is absent, say so.\n\nContext:\n" + context + "\n\nQuestion: " + question)
        try:
            response = requests.post(LLM_API_URL, headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                                     json={"model": LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}, timeout=20)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
            return None


llm_service = LLMService()
