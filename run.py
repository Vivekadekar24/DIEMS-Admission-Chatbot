
from backend.app import app
from backend.utils.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    print("DIEMS Admission Chatbot starting...")
    print(f"Open http://{HOST}:{PORT} in your browser")

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG
    )
