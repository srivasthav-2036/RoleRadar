# RoleRadar 

**RoleRadar is an AI-powered job matching platform.** You upload your resume, and it automatically finds job listings that match your skills and experience — then emails you the results.

> 🌐 Live at: [tryroleradar.vercel.app](https://tryroleradar.vercel.app)

---

## What does it do?

1. **You upload your resume** — RoleRadar reads and understands it using AI.
2. **It fetches fresh job listings** — every 4 hours, it pulls new jobs from multiple providers.
3. **It matches jobs to your resume** — using vector search + AI scoring to find the best fits.
4. **It emails you the top matches** — so you don't have to check back manually.
5. **You can tailor your resume** — for any job, with one click, and download it as a PDF.

---

## Features

-  **Resume Upload & Parsing** — Upload a PDF resume; AI extracts your skills, experience, and projects
-  **Smart Job Matching** — Hybrid matching using vector embeddings + LLM scoring (0–100)
-  **Email Notifications** — Get notified when new matching jobs are found
-  **AI Resume Tailoring** — Generate a tailored resume for any job listing, downloadable as PDF
-  **Dashboard** — See your top job recommendations and match scores in one place
-  **Auth** — Secure login & registration with JWT tokens and bcrypt password hashing

---

## Tech Stack

### Frontend
| Tool | Purpose |
|------|---------|
| Next.js 14 | React framework |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| Vercel | Hosting |

### Backend
| Tool | Purpose |
|------|---------|
| FastAPI | REST API |
| Python 3.11 | Backend language |
| TiDB Cloud | MySQL-compatible cloud database with vector search |
| Docker | Containerization |

### AI & APIs
| Service | Used For |
|---------|---------|
| Google Gemini | Resume tailoring |
| Groq (LLaMA) | Resume extraction, JD parsing, Semantic job matching |
| Jina AI | Text embeddings |
| Adzuna API | Job listings |
| RapidAPI (JSearch) | Job listings |
| Brevo | Sending transactional emails |

---

## Project Structure

```
RoleRadar/
├── frontend/               # Next.js web app
│   ├── app/
│   │   ├── dashboard/      # Main dashboard pages
│   │   ├── login/          # Login page
│   │   ├── register/       # Registration page
│   │   └── forgot-password/
│   └── components/         # Reusable UI components
│
├── backend/                # FastAPI Python backend
│   ├── api/
│   │   └── routers/        # API route handlers
│   │       ├── auth.py         # Login, register, password reset
│   │       ├── resumes.py      # Resume upload & management
│   │       ├── recommendations.py  # Job recommendations
│   │       ├── tailoring.py    # Resume tailoring
│   │       └── dashboard.py    # Dashboard data
│   │
│   ├── job_fetcher/        # Fetches jobs from Adzuna & JSearch
│   ├── resume_extractor/   # Parses uploaded PDF resumes with AI
│   ├── embedder/           # Creates vector embeddings for resumes & jobs
│   ├── similarity_engine/  # LLM-based job vs resume scoring
│   ├── recommender/        # Recommendation pipeline (vector + LLM)
│   ├── resume_tailoring/   # AI resume tailoring + PDF generation
│   ├── notifications/      # Email sending via Brevo
│   ├── maintenance/        # Scheduled pipeline (runs every 4 hours)
│   ├── auth/               # JWT auth helpers
│   ├── database/           # DB connection & models
│   ├── rate_limiting/      # API usage/budget tracking
│   └── Dockerfile
│
└── .github/
    └── workflows/
        ├── scheduled_pipeline.yml  # Runs the job fetch + recommend pipeline every 4 hours
        └── daily_cleanup.yml       # Cleans up old job listings daily
```

---

## How the Recommendation Pipeline Works

Every 4 hours, a GitHub Actions job runs automatically:

```
1. Collect all unique job search queries from uploaded resumes
        ↓
2. Fetch fresh job listings from Adzuna & JSearch
        ↓
3. For each user:
    a. Get their resume embedding
    b. Run vector search to find the closest job matches
    c. Filter by distance threshold (free, no API cost)
    d. Send survivors to Groq LLM for detailed scoring (0-100)
    e. Keep only jobs scoring 60 or above
    f. Store top 15 results
    g. Send email notification
```

This hybrid approach keeps API costs low — the cheap vector search filters out bad matches before the expensive LLM even runs.

---

## Getting Started (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- A TiDB Cloud account (free tier works)
- API keys (see Environment Variables section below)

### 1. Clone the repo

```bash
git clone https://github.com/srivasthav-2036/RoleRadar.git
cd RoleRadar
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt
```

Create a `.env` file in the project root (see Environment Variables below).

Run the API server:
```bash
# Run from the project root
uvicorn backend.api.main:app --reload
```

The API will be available at http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

---

## Environment Variables

Create a `.env` file in the project root with the following:

```env
# JWT (generate a random secret — any long random string works)
JWT_SECRET_KEY=your_jwt_secret_here

# Job APIs
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_API_KEY=your_adzuna_api_key
RAPIDAPI_KEY=your_rapidapi_key         # for JSearch

# AI APIs
GROQ_API_KEY=your_groq_key
GROQ_API_KEY_FOR_JD_PARSING=your_groq_key
GROQ_API_KEY_FOR_SEMANTIC_MATCHING=your_groq_key
JINA_API_KEY=your_jina_key
GEMINI_API_KEY_FOR_TAILORING=your_gemini_key

# TiDB Cloud Database
TIDB_HOST=your_tidb_host
TIDB_PORT=4000
TIDB_USER=your_tidb_user
TIDB_PASSWORD=your_tidb_password
TIDB_DATABASE=roleradar
TIDB_CA=backend/certs/isrgrootx1.pem

# Email (Brevo — free tier: 300 emails/day, no credit card needed)
BREVO_API_KEY=your_brevo_api_key
BREVO_SENDER_EMAIL=your_verified_sender@example.com

# Your deployed frontend URL (used in email links)
WEBSITE_BASE_URL=https://tryroleradar.vercel.app
```

### Where to get these keys

| Service | Link | Free Tier? |
|---------|------|-----------|
| Adzuna | https://developer.adzuna.com | Yes |
| RapidAPI (JSearch) | https://rapidapi.com | Yes |
| Groq | https://console.groq.com | Yes |
| Jina AI | https://jina.ai | Yes |
| Google Gemini | https://aistudio.google.com | Yes |
| TiDB Cloud | https://tidbcloud.com | Yes |
| Brevo | https://brevo.com | Yes (300 emails/day) |

---

## Running with Docker

```bash
cd backend
docker build -t roleradar-backend .
docker run -p 8000:8000 --env-file ../.env roleradar-backend
```

---

## Running the Scheduled Pipeline Manually

```bash
# From the project root
python -m backend.maintenance.scheduled_run
```

This does the full cycle: fetch jobs → generate recommendations → send emails.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| POST | /api/auth/register | Create a new account |
| POST | /api/auth/login | Login and get a JWT token |
| POST | /api/resumes/upload | Upload your resume (PDF) |
| GET  | /api/recommendations | Get your job recommendations |
| POST | /api/tailoring/tailor | Generate a tailored resume for a job |
| GET  | /api/dashboard | Get dashboard summary data |

Interactive API docs are available at http://localhost:8000/docs when running locally.

---

## Deployment

- **Frontend** — Deployed on Vercel. 
- **Backend** — Containerised with Docker and deployed live on Render.
- **Scheduled Jobs** — Handled by GitHub Actions (`.github/workflows/scheduled_pipeline.yml`). No extra infrastructure needed.

---

## License

This project is for personal/educational use.

---

*Built with love by Srivasthav*
