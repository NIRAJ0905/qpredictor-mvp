# Q-Predictor — GitHub + Render + Vercel Deployment Guide

---

## Step 1 — Prepare your local project

Replace these files in your project with the updated versions provided:

```
backend/app/database.py        ← auto-switches SQLite ↔ PostgreSQL
backend/app/main.py            ← CORS updated for Vercel
backend/requirements.txt       ← psycopg2-binary added
backend/src/lib/api.js         ← reads VITE_API_URL for production
frontend/vite.config.js        ← clean build config
render.yaml                    ← goes in ROOT of project (next to backend/)
vercel.json                    ← goes in frontend/ folder
.gitignore                     ← goes in ROOT of project
```

Make sure `backend/storage/papers/.gitkeep` exists (empty file):
```bash
# Run from inside backend/ folder
mkdir -p storage/papers
type nul > storage\papers\.gitkeep
```

---

## Step 2 — Push to GitHub

Open a terminal in your project root folder (the one containing `backend/` and `frontend/`):

```bash
# Initialize git repo
git init

# Stage everything
git add .

# First commit
git commit -m "Initial commit — Q-Predictor MVP"

# Create repo on GitHub:
# Go to github.com → click + → New repository
# Name it: qpredictor
# Set to Public or Private (your choice)
# Do NOT initialize with README (we already have files)
# Click Create repository

# Copy the repo URL from GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/qpredictor.git
git branch -M main
git push -u origin main
```

After this, your code is on GitHub at:
`https://github.com/YOUR_USERNAME/qpredictor`

---

## Step 3 — Deploy Backend on Render

1. Go to **https://render.com** and sign in (or create free account)

2. Click **New** → **Blueprint**

3. Connect your GitHub account when prompted

4. Select your `qpredictor` repository

5. Render will find `render.yaml` automatically and show:
   - `qpredictor-backend` (Web Service)
   - `qpredictor-db` (PostgreSQL database)

6. Click **Apply** — Render will:
   - Create a free PostgreSQL database
   - Deploy your FastAPI backend
   - Auto-generate a JWT_SECRET_KEY
   - Wire DATABASE_URL automatically

7. Wait ~5 minutes for the first deploy. You'll see build logs.

8. Once deployed, your backend URL will be something like:
   `https://qpredictor-backend.onrender.com`

9. Test it: open `https://qpredictor-backend.onrender.com/api/health`
   Should return: `{"status": "ok", ...}`

10. Also visit: `https://qpredictor-backend.onrender.com/docs`
    Full Swagger UI works in production too.

### Important: Tesseract on Render

Render's free tier runs Ubuntu. Add this build command in render.yaml or
in the Render dashboard under "Build Command":

```
apt-get install -y tesseract-ocr && pip install -r requirements.txt
```

To do this in the Render dashboard:
- Go to your service → Settings → Build Command
- Change to: `apt-get install -y tesseract-ocr && pip install -r requirements.txt`
- Click Save → this triggers a redeploy

---

## Step 4 — Deploy Frontend on Vercel

1. Go to **https://vercel.com** and sign in with GitHub

2. Click **Add New** → **Project**

3. Find and select your `qpredictor` repository

4. Vercel will ask for configuration:
   - **Root Directory**: set to `frontend`
   - **Framework Preset**: Vite (auto-detected)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

5. Add environment variable:
   - Click **Environment Variables**
   - Name: `VITE_API_URL`
   - Value: `https://qpredictor-backend.onrender.com`
     (replace with your actual Render URL from Step 3)

6. Click **Deploy**

7. After ~2 minutes your frontend is live at:
   `https://qpredictor.vercel.app` (or similar)

8. Set `FRONTEND_URL` on Render:
   - Go to Render → your backend service → Environment
   - Add: `FRONTEND_URL` = `https://qpredictor.vercel.app`
   - Click Save (triggers redeploy)

---

## Step 5 — Test the live app

1. Open your Vercel URL
2. Sign up for a new account
3. Create a subject and upload papers
4. Run predictions

---

## Updating the app later

Any time you push changes to GitHub, both Render and Vercel
auto-redeploy within ~3 minutes:

```bash
git add .
git commit -m "Fix: improved prediction accuracy"
git push
```

---

## Free tier limits to know

| Service | Limit |
|---------|-------|
| Render backend | Spins down after 15 min inactivity — first request takes ~30s to wake up |
| Render PostgreSQL | 1GB storage, expires after 90 days on free tier |
| Vercel frontend | 100GB bandwidth/month — more than enough |

To avoid the Render sleep, you can ping `/api/health` every 10 minutes
using a free service like https://cron-job.org

---

## Local dev (unchanged)

```bash
# Terminal 1
cd backend
uvicorn app.main:app --reload

# Terminal 2
cd frontend
npm run dev
```

Local still uses SQLite — no Postgres needed locally.
