# Q-Predictor Frontend

React + Vite + Tailwind dashboard for the AI Question Paper Predictor.

## Requirements
- Node.js 18+ (check: `node --version`)
- Backend running on `http://127.0.0.1:8000`

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open → **http://localhost:5173**

The Vite dev server proxies all `/api` calls to `http://127.0.0.1:8000`
so CORS is never an issue during development.

## Pages

| Route          | Page           | Description                        |
|----------------|----------------|------------------------------------|
| `/`            | Landing        | Marketing / intro page             |
| `/signup`      | Signup         | Create account                     |
| `/login`       | Login          | Login, get JWT                     |
| `/dashboard`   | Dashboard      | Subject list + stats               |
| `/upload`      | Upload         | Drag-drop PDF upload               |
| `/analysis`    | Analysis       | Charts: topic frequency, unit pie  |
| `/predictions` | Predictions    | Ranked predicted questions         |
| `/chat`        | AI Chat        | Ask questions about your papers    |

## Build for production

```bash
npm run build
# Output in dist/ — serve with any static host
```
