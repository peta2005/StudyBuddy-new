# Load environment variables
import os
from dotenv import load_dotenv

from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Load .env before any module reads environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.db import init_db
from utils.pdf_utils import extract_text_per_page
from utils.embedding_utils import create_vector_store
from utils.query_utils import query_vector_db
from utils.auth_utils import require_auth, is_auth_configured
from utils.rate_limit import limiter, user_or_ip_key
from utils.security_utils import (
    MAX_UPLOAD_BYTES,
    user_upload_dir,
    user_vector_dir,
    validate_pdf_upload,
)
from utils.user_store import save_message, get_user_sessions, get_session_messages, delete_session
from routes.auth_routes import auth_bp, init_oauth
from groq import Groq

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found. Please check your .env file.")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY") or os.getenv("JWT_SECRET") or "dev-change-me"
init_db()

# Preload embedding model on startup so uploads/questions don't wait for it
from utils.embedding_utils import get_embedding_model
try:
    logger.info("Preloading embedding model...")
    get_embedding_model()
    logger.info("Embedding model preloaded successfully!")
except Exception as preload_exc:
    logger.exception("Failed to preload embedding model: %s", preload_exc)

frontend_origins = os.getenv(
    "FRONTEND_URL",
    "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173",
).split(",")
CORS(
    app,
    origins=[origin.strip() for origin in frontend_origins if origin.strip()],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
    methods=["GET", "POST", "DELETE", "OPTIONS"],
    max_age=3600,
)

limiter.init_app(app)
init_oauth(app)
app.register_blueprint(auth_bp)

BACKEND_ROOT = Path(__file__).resolve().parent
UPLOAD_FOLDER = str(BACKEND_ROOT / "uploads")
VECTOR_FOLDER = str(BACKEND_ROOT / "vector_store")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VECTOR_FOLDER, exist_ok=True)

client = Groq(api_key=api_key)


def ask_ai(question, context=None):
    if context:
        user_prompt = f"""
You are a helpful study assistant.

Use the following context to answer the question.

Context:
{context}

Question:
{question}

CRITICAL INSTRUCTIONS:
- If the context is not relevant to the question, or if the question is a general greeting or general knowledge question that does not require this specific context, you MUST start your response with '[GENERAL]' on the very first line, and then answer the question normally without using the context.
- If the context is relevant and you use it to answer the question, you MUST start your response with '[CONTEXTUAL]' on the very first line.
"""
    else:
        user_prompt = question

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are 'Smart Study Buddy', a helpful AI study assistant created to help users query and analyze their documents. Always follow formatting instructions precisely."},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    return response.choices[0].message.content



@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "StudyBuddy backend is running successfully",
        "auth_enabled": is_auth_configured(),
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "auth_enabled": is_auth_configured()})


@app.route("/upload", methods=["POST"])
@require_auth
@limiter.limit("10 per minute", key_func=user_or_ip_key)
def upload_pdf():
    try:
        if "pdf" not in request.files:
            return jsonify({"error": "No PDF file uploaded"}), 400

        file = request.files["pdf"]
        filename, _ = validate_pdf_upload(file, request.content_length)

        user_dir = user_upload_dir(UPLOAD_FOLDER, request.user_id)
        store_dir = user_vector_dir(VECTOR_FOLDER, request.user_id)
        file_path = os.path.join(user_dir, filename)

        file.save(file_path)

        pages = extract_text_per_page(file_path)
        if not pages:
            return jsonify({"error": "Could not extract text from PDF."}), 400

        create_vector_store(pages, store_dir=store_dir)

        return jsonify({
            "message": "Document uploaded successfully",
            "filename": filename,
        })

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("Upload failed: %s", exc)
        return jsonify({"error": "Upload failed. Please try again or restart the backend."}), 500


@app.route("/ask", methods=["POST"])
@require_auth
@limiter.limit("20 per minute", key_func=user_or_ip_key)
def ask_question():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        query = (data.get("query") or "").strip()
        if not query:
            return jsonify({"error": "Query is required"}), 400
        if len(query) > 4000:
            return jsonify({"error": "Query is too long."}), 400

        session_id = (data.get("session_id") or "").strip()
        session_title = (data.get("session_title") or "New Chat").strip()

        store_dir = user_vector_dir(VECTOR_FOLDER, request.user_id)
        passages = query_vector_db(query, store_dir=store_dir)

        if not passages:
            return jsonify({
                "answer": "Upload a PDF first so I can answer questions from your document.",
                "sources": [],
            })

        context = "\n\n".join(
            [f"Page {p['page']}:\n{p['text']}" for p in passages]
        )

        raw_answer = ask_ai(query, context=context)

        # Parse LLM response tags to decide if we should return sources
        is_contextual = True
        answer = raw_answer.strip()
        if answer.startswith("[GENERAL]"):
            is_contextual = False
            answer = answer[len("[GENERAL]"):].strip()
        elif answer.startswith("[CONTEXTUAL]"):
            is_contextual = True
            answer = answer[len("[CONTEXTUAL]"):].strip()

        # Compile and deduplicate sources if context was relevant
        sources = []
        if is_contextual:
            seen_pages = set()
            for passage in passages:
                page = passage.get("page")
                if page is not None and page not in seen_pages:
                    seen_pages.add(page)
                    sources.append({
                        "page": page,
                        "excerpt": (passage.get("text") or "")[:240],
                    })


        # Save to chat history if session_id provided
        if session_id:
            try:
                save_message(request.user_id, session_id, session_title, "user", query)
                save_message(request.user_id, session_id, session_title, "assistant", answer, sources)
            except Exception as hist_exc:
                logger.warning("Failed to save chat history: %s", hist_exc)

        return jsonify({"answer": answer, "sources": sources})

    except Exception as exc:
        logger.exception("ASK ROUTE ERROR: %s", exc)
        return jsonify({"error": "Failed to process question."}), 500


@app.route("/history/sessions", methods=["GET"])
@require_auth
@limiter.limit("60 per minute", key_func=user_or_ip_key)
def history_sessions():
    try:
        sessions = get_user_sessions(request.user_id)
        return jsonify({"sessions": sessions})
    except Exception as exc:
        logger.exception("Failed to fetch sessions: %s", exc)
        return jsonify({"error": "Failed to fetch history."}), 500


@app.route("/history/sessions/<session_id>", methods=["GET"])
@require_auth
@limiter.limit("60 per minute", key_func=user_or_ip_key)
def history_session_messages(session_id: str):
    try:
        messages = get_session_messages(request.user_id, session_id)
        return jsonify({"messages": messages})
    except Exception as exc:
        logger.exception("Failed to fetch session messages: %s", exc)
        return jsonify({"error": "Failed to fetch session."}), 500


@app.route("/history/sessions/<session_id>", methods=["DELETE"])
@require_auth
@limiter.limit("30 per minute", key_func=user_or_ip_key)
def history_delete_session(session_id: str):
    try:
        delete_session(request.user_id, session_id)
        return jsonify({"message": "Session deleted."})
    except Exception as exc:
        logger.exception("Failed to delete session: %s", exc)
        return jsonify({"error": "Failed to delete session."}), 500


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug, threaded=True)
