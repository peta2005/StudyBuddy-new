# Smart Study Buddy 📚🤖

Smart Study Buddy is a secure, high-performance PDF-based question-answering assistant. It uses a **Retrieval-Augmented Generation (RAG)** pipeline to index PDF documents and answer user queries with precise page citations.

The project features a lightweight Python Flask backend and a modern React TypeScript frontend styled with a clean glassmorphic theme.

---

##  Key Features

* **Instant PDF Processing:** Extracts text from uploaded PDFs, builds vector embeddings, and indexes them using **FAISS** for fast similarity search.
* **Intelligent Answering:** Queries the **Groq Cloud API** using `llama-3.3-70b-versatile` for high-quality, contextual summaries.
* **Relevance-Aware Citations:** Automatically detects whether queries are general or contextual, displaying source page citations only when document facts were used.
* **Branded Custom Assistant:** Pre-configured identity as *Smart Study Buddy* rather than a generic LLM.
* **Authentication & Chat History:** Local database auth (MySQL/SQLite) and persistent session history.
* **Clean Modern UI:** Interactive chat view, responsive sidebar, document management, and dark/light modes.

---

##  Tech Stack

### Frontend
* **Core:** React 18 + TypeScript + Vite
* **Styling:** Tailwind CSS + Radix UI (Shadcn)
* **API Client:** Fetch API client with authorization headers

### Backend
* **Framework:** Flask with CORS and Rate Limiting
* **Embeddings:** SentenceTransformers (`all-MiniLM-L6-v2`)
* **Vector Index:** FAISS (Facebook AI Similarity Search)
* **Text Extraction:** PyMuPDF + Tesseract OCR (with OS check fallback)
* **Database:** MySQL (supported via `PyMySQL`) / SQLite fallback
* **LLM Engine:** Groq SDK (Llama 3.3)

---

##  Local Setup

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend/` folder based on `.env.example` and fill in:
   * `GROQ_API_KEY`: Your Groq API key.
   * `JWT_SECRET` / `SUPABASE_JWT_SECRET`: For session security.
   * MySQL database credentials (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
5. Run the development server:
   ```bash
   python app.py
   ```

### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `frontend/` folder:
   ```env
   VITE_API_URL=http://127.0.0.1:5000
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```
5. Open `http://localhost:5173` in your browser.

---

##  Production Deployment

### 1. Frontend (Vercel)
Connect your GitHub repository to [Vercel](https://vercel.com/) and deploy the `frontend/` directory. Set the `VITE_API_URL` environment variable to your production backend URL.

### 2. Backend (Render / Railway)
Deploy the `backend/` directory to [Render](https://render.com/) or [Railway](https://railway.app/). 
* Set your environment variables in their dashboard.
* If using Render's free tier, note that file storage is ephemeral (re-uploaded PDFs will reset on restarts). For persistent storage, Railway or a Render paid volume is recommended.

### 3. Database (Aiven / Clever Cloud)
Provision a free managed MySQL database on Aiven or Clever Cloud and paste the database URL/credentials into your backend's environment variables.
