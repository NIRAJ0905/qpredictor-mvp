# AI Question Paper Analyzer & Predictor — Backend

Analyze previous-year exam PDFs and predict important questions for upcoming exams.

---

## Quick start (2 commands)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** — the full Swagger UI is ready immediately.

**No Docker. No PostgreSQL. No Alembic. No migrations.**
The SQLite database is created automatically at `backend/qpredictor.db` on first run.

---

## Tech stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Framework   | FastAPI + Uvicorn                   |
| Database    | SQLite (via SQLAlchemy 2.x)         |
| Auth        | JWT (python-jose) + bcrypt          |
| PDF parsing | PyMuPDF (primary) + pdfplumber (fallback) |
| NLP         | scikit-learn TF-IDF + cosine similarity |

---

## Workflow

```
1. POST /api/auth/signup          — create account
2. POST /api/auth/login           — get bearer token
                                    (use email as "username" in the form)
3. POST /api/subjects             — create a subject (e.g. "Applied Physics")
4. POST /api/subjects/{id}/upload-papers
                                  — upload ≥10 PDFs
                                    (questions are extracted immediately)
5. GET  /api/subjects/{id}/analysis
                                  — view frequency & topic analysis
6. POST /api/subjects/{id}/predictions
                                  — run the prediction engine
7. GET  /api/subjects/{id}/predictions
                                  — view ranked predictions with confidence %
8. POST /api/chat                 — ask the chatbot about your papers
```

---

## Full API reference

### Auth
| Method | URL                  | Auth | Body / Form                        |
|--------|----------------------|------|-------------------------------------|
| POST   | `/api/auth/signup`   | No   | `{name, email, password}`          |
| POST   | `/api/auth/login`    | No   | form: `username=<email>&password=` |
| GET    | `/api/auth/me`       | Yes  | —                                   |

### Subjects
| Method | URL                       | Auth | Body                                       |
|--------|---------------------------|------|--------------------------------------------|
| POST   | `/api/subjects`           | Yes  | `{name, code?, department?, university?, semester?}` |
| GET    | `/api/subjects`           | Yes  | —                                          |
| GET    | `/api/subjects/{id}`      | Yes  | —                                          |
| DELETE | `/api/subjects/{id}`      | Yes  | —                                          |

### Papers
| Method | URL                                         | Auth | Notes                        |
|--------|---------------------------------------------|------|------------------------------|
| POST   | `/api/subjects/{id}/upload-papers`          | Yes  | multipart: `files[]`, `year?`, `semester?` |
| POST   | `/api/subjects/{id}/process`                | Yes  | Re-run extraction on failed papers |
| GET    | `/api/subjects/{id}/papers`                 | Yes  | —                            |
| DELETE | `/api/subjects/{id}/papers/{paper_id}`      | Yes  | —                            |

### Analysis
| Method | URL                             | Auth | Notes               |
|--------|---------------------------------|------|---------------------|
| GET    | `/api/subjects/{id}/analysis`   | Yes  | Full frequency report |
| GET    | `/api/subjects/{id}/questions`  | Yes  | `?limit=100&offset=0` |

### Predictions
| Method | URL                               | Auth | Notes                         |
|--------|-----------------------------------|------|-------------------------------|
| POST   | `/api/subjects/{id}/predictions`  | Yes  | Run engine, returns results   |
| GET    | `/api/subjects/{id}/predictions`  | Yes  | Fetch last generated results  |

### Chat
| Method | URL          | Auth | Body                         |
|--------|--------------|------|------------------------------|
| POST   | `/api/chat`  | Yes  | `{subject_id, message}`      |

Sample questions for chat:
- "What should I study first?"
- "What are the most repeated topics?"
- "What questions are likely in Unit 3?"
- "Give me a revision plan"
- "What are the top predicted questions?"

### Health
| Method | URL            | Auth |
|--------|----------------|------|
| GET    | `/api/health`  | No   |

---

## Example `curl` walkthrough

```bash
BASE=http://localhost:8000

# 1. Sign up
curl -s -X POST $BASE/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Asha","email":"asha@test.com","password":"secret123"}' | python3 -m json.tool

# 2. Login — note form data, not JSON
TOKEN=$(curl -s -X POST $BASE/api/auth/login \
  -d "username=asha@test.com&password=secret123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: $TOKEN"

# 3. Create subject
SUBJECT=$(curl -s -X POST $BASE/api/subjects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Applied Physics","code":"PHY101","university":"Mumbai University","semester":"Sem 2"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Subject ID: $SUBJECT"

# 4. Upload papers (upload all your PDFs in one request)
curl -s -X POST $BASE/api/subjects/$SUBJECT/upload-papers \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@paper_2019.pdf" \
  -F "files=@paper_2020.pdf" \
  -F "files=@paper_2021.pdf" \
  ... \
  | python3 -m json.tool

# 5. Run predictions
curl -s -X POST $BASE/api/subjects/$SUBJECT/predictions \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 6. Chat
curl -s -X POST $BASE/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"subject_id\":$SUBJECT,\"message\":\"What should I study first?\"}" \
  | python3 -m json.tool
```

---

## Prediction scoring

The confidence score is a weighted combination:

| Component        | Weight | What it measures                              |
|------------------|--------|-----------------------------------------------|
| Frequency score  | 40%    | How many papers the question appeared in      |
| Recency score    | 20%    | Whether it appeared in recent years           |
| Marks score      | 20%    | High-mark questions weighted up               |
| Topic spread     | 10%    | Appeared across multiple units/sections       |
| Year variety     | 10%    | Spread across different years (not just one)  |

---

## File structure

```
backend/
├── app/
│   ├── main.py            # FastAPI app, lifespan, router registration
│   ├── database.py        # SQLite engine, session, Base, init_db()
│   ├── models.py          # All ORM tables (User, Subject, Paper, Question, Prediction)
│   ├── schemas.py         # All Pydantic request/response schemas
│   ├── auth.py            # JWT + bcrypt utilities + get_current_user dependency
│   ├── pdf_processor.py   # PDF text extraction + question parsing
│   ├── predictor.py       # TF-IDF grouping + scoring + prediction engine
│   └── routers/
│       ├── auth.py
│       ├── subjects.py
│       ├── papers.py
│       ├── analysis.py
│       ├── predictions.py
│       └── chat.py
├── storage/
│   └── papers/            # Uploaded PDFs stored here (organised by subject_id)
├── qpredictor.db          # SQLite DB (auto-created on first run, gitignored)
├── requirements.txt
└── README.md
```

---

## Reset the database

```bash
rm backend/qpredictor.db
# restart uvicorn — tables are recreated automatically
```

---

## Environment variables (optional)

The app runs with zero configuration. For production, set these:

```bash
export JWT_SECRET_KEY="your-long-random-secret"
export ACCESS_TOKEN_EXPIRE_MINUTES="1440"
```

---

## Upgrading later

| Feature                  | What to add                                     |
|--------------------------|-------------------------------------------------|
| Background processing    | FastAPI `BackgroundTasks` or Celery             |
| Better NLP               | sentence-transformers embeddings                |
| PostgreSQL               | Change `DATABASE_URL`, add pgvector, Alembic    |
| Docker                   | Add `Dockerfile` + `docker-compose.yml`         |
| Frontend                 | React + Vite (Phase 2)                          |
| MCQ generator            | New router using existing Question data         |
| PDF report export        | ReportLab                                       |
