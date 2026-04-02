# 🎓 LearnAI — AI Student Learning Platform

A full-stack AI-powered student learning platform built with **Flask** + **Next.js**, using **Google Gemini (FREE)** for AI features.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **Auth** | Register, Login, Logout, Forgot/Reset Password (SMTP) |
| 💬 **AI Chat** | Gemini-powered chatbot with RAG, chat history, TTS |
| 📝 **Smart Notes** | AI-generated notes, PDF export, refine (summary/Q&A/mindmap) |
| 📚 **Resources** | Upload/share resources, comments, admin moderation, dedup |
| 🎬 **YouTube Mindmap** | Paste URL → transcript → Mermaid mindmap |
| 📄 **Resume Analyzer** | Upload PDF/DOCX → AI analysis with ATS tips |
| ⚙️ **Admin Panel** | User mgmt, leaderboard, resource moderation, DB explorer |
| 🧠 **Knowledge Base** | Structured content for RAG-enhanced chatbot |

## 🛠️ Tech Stack

- **Frontend**: Next.js 14 (App Router), Tailwind CSS, Shadcn UI
- **Backend**: Flask, SQLAlchemy, SQLite
- **AI**: Google Gemini (FREE tier), sentence-transformers (local embeddings), FAISS
- **HTTP**: Native `fetch` (no axios)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) Google Gemini API key — [Get free key](https://aistudio.google.com/apikey)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Backend runs at: `http://localhost:5000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:3000`

### 3. Environment Variables

**Backend** (`backend/.env`):
```env
SECRET_KEY=your-random-secret-key
GEMINI_API_KEY=your-free-gemini-key        # Optional, AI features degrade gracefully
MAIL_SERVER=smtp.gmail.com                 # For password reset emails
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
FRONTEND_URL=http://localhost:3000
```

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

## 📡 API Endpoints

| Module | Prefix | Key Endpoints |
|--------|--------|---------------|
| Auth | `/api/auth` | register, login, logout, me, forgot-password, reset-password |
| Chat | `/api/chat` | sessions (CRUD), messages (send/list) |
| Notes | `/api/notes` | generate, list, update, delete, refine, export-pdf |
| Resources | `/api/resources` | upload, list, approve/reject, comments |
| YouTube | `/api/youtube` | mindmap (URL → Mermaid) |
| Resume | `/api/resume` | analyze (file upload) |
| Admin | `/api/admin` | users, leaderboard, stats, db-query |
| KB | `/api/kb` | entries (CRUD), search |

## 📁 Project Structure

```
ai-student-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── auth/routes.py       # Auth endpoints
│   │   ├── chat/routes.py       # Chat + AI
│   │   ├── notes/routes.py      # Notes + AI
│   │   ├── resources/routes.py  # Resources + comments
│   │   ├── youtube/routes.py    # YouTube transcript → mindmap
│   │   ├── resume/routes.py     # Resume analyzer
│   │   ├── admin/routes.py      # Admin panel
│   │   ├── kb/routes.py         # Knowledge base
│   │   └── utils/
│   │       ├── ai_helpers.py    # Gemini AI integration
│   │       ├── file_parser.py   # PDF/DOCX parsing
│   │       ├── rag.py           # FAISS + RAG pipeline
│   │       └── decorators.py    # Auth decorators
│   ├── config.py
│   ├── app.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Root layout
│   │   │   ├── page.tsx             # Landing page
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── forgot-password/page.tsx
│   │   │   ├── reset-password/page.tsx
│   │   │   └── dashboard/
│   │   │       ├── layout.tsx       # Sidebar layout
│   │   │       ├── page.tsx         # Home dashboard
│   │   │       ├── chat/page.tsx    # AI Chatbot
│   │   │       ├── notes/page.tsx   # Notes
│   │   │       ├── resources/page.tsx
│   │   │       ├── youtube/page.tsx # Mindmap generator
│   │   │       ├── resume/page.tsx  # Resume analyzer
│   │   │       └── admin/page.tsx   # Admin panel
│   │   ├── components/ui/          # Shadcn components
│   │   └── lib/
│   │       ├── api.ts              # Fetch-based API client
│   │       ├── auth.tsx            # Auth context
│   │       └── utils.ts
│   └── .env.local
└── README.md
```

## 🔑 First User = Admin

The first user to register automatically gets the **admin** role. All subsequent users are **students** by default.

## 💰 Cost: $0

Everything is 100% free:
- **Google Gemini**: 15 requests/min, 1M tokens/day free
- **sentence-transformers**: Local embeddings, no API needed
- **FAISS**: Local vector database
- **youtube-transcript-api**: Free transcript fetching
- **SQLite**: File-based database

## License

MIT
