# Supabase Authentication Setup

## 1. Create a Supabase project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Create a new project
3. Open **Project Settings → API**

Copy these values:

| Value | Use in |
|-------|--------|
| Project URL | `VITE_SUPABASE_URL` (frontend) |
| anon public key | `VITE_SUPABASE_ANON_KEY` (frontend) |
| JWT Secret | `SUPABASE_JWT_SECRET` (backend only) |

## 2. Configure environment files

### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://127.0.0.1:5000
VITE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_ANON_KEY
```

### Backend (`backend/.env`)

```env
GROQ_API_KEY=your-groq-key
SUPABASE_JWT_SECRET=your-jwt-secret
FRONTEND_URL=http://localhost:5173,http://127.0.0.1:5173
FLASK_DEBUG=false
```

## 3. Install dependencies

```bash
# Frontend
cd frontend
npm install

# Backend
cd backend
pip install -r requirements.txt
```

## 4. Enable email auth in Supabase

1. Open **Authentication → Providers**
2. Enable **Email**
3. For local testing, you can disable **Confirm email** under Email provider settings

## 5. Security checklist

- Never commit `.env` files
- Never put `SUPABASE_JWT_SECRET` or `GROQ_API_KEY` in the frontend
- Only the Supabase **anon** key belongs in the frontend
- `/upload` and `/ask` require a valid Supabase JWT
- PDFs and vector indexes are stored per user ID
- CORS is restricted to `FRONTEND_URL`
- Uploads are limited to 50MB and validated as real PDFs

## 6. Run the app

```bash
# Terminal 1
cd backend
python app.py

# Terminal 2
cd frontend
npm run dev
```

Sign up, sign in, then upload a PDF and ask questions.
