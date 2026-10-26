
from flask import Flask, send_from_directory
from backend.utils.config import FRONTEND_DIR
from backend.routes.chat import chat_bp


def create_app():
    app = Flask(
        __name__,
        static_folder=None
    )

    app.register_blueprint(chat_bp)

    @app.get("/")
    def home():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.get("/<path:filename>")
    def frontend_files(filename):
        return send_from_directory(FRONTEND_DIR, filename)

    @app.get("/api/health")
    def health():
        from backend.services.retriever import retriever
        return {"status": "ok", "project": "DIEMS Admission Chatbot", "index_ready": retriever.ready, "records": retriever.record_count}

    return app


app = create_app()
