# 🔴 Red Button

**Red Button** is a full-stack AI application that automates subcontractor outreach for construction estimators.  
It streamlines the workflow of analyzing construction plans, identifying relevant trades, and generating targeted solicitation emails.

---

## 🚧 Status

**MVP in development.**  
- Backend (FastAPI + Python) is functional: PDF upload, AI-based trade extraction, trade normalization, and contact matching.  
- Frontend (React + Vite) provides UI for job creation, file upload, trade review, and email preview.  
- Documentation and vertical slices are tracked in [`docs/`](docs/).

---

## ✨ Features (Planned MVP)

- Upload PDF plan sets and split into images  
- Use AI (OpenAI GPT-4) to extract trade scopes  
- Normalize trade names to standard schema  
- Match trades to subcontractor contacts from user database  
- Generate and preview customized solicitation emails  
- Send emails via SendGrid (or compatible service)  
- View email delivery logs per job  
- Export job summaries as JSON or CSV  

---

## 🧱 Tech Stack

| Layer        | Technology                |
|--------------|---------------------------|
| **Frontend** | React (Vite, TypeScript)  |
| **Backend**  | FastAPI (Python 3.12)     |
| **AI Engine**| OpenAI GPT-4 API          |
| **Email**    | SendGrid (planned)        |
| **Database** | SQLite (MVP), PostgreSQL (planned) |
| **Deployment** | Docker + Docker Compose (planned) |
| Billing      | Stripe *(planned)*        |

---

## 🚀 Quickstart

### Backend

```bash
# create and activate virtualenv (Windows example)
python -m venv .venv
.venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# copy example env and set your own values
cp .env.example .env

# run server
uvicorn backend.main:app --reload --port 8001

```
### Frontend

```bash
cd frontend
npm install
npm run dev

Open http://localhost:5173
 in your browser.
```

## ⚙️ Environment Variables
Copy .env.example → .env and fill in your values:

```bash
# Backend
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o

# Frontend
VITE_API_BASE_URL=http://localhost:8001

```

## 📄 Documentation

- [System Architecture](docs/architecture.md)
- [Software Requirements Specification](docs/srs.md)
- [Proposed File Structure](docs/file_structure.md)
- [UML Diagrams](docs/uml/)


## 📁 Repository Structure

```bash
redbutton/
├── backend/        # FastAPI app, core logic, services
├── frontend/       # React (Vite) app
├── docs/           # Architecture, SRS, vertical slices, UML diagrams
├── tests/          # Backend tests
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE (Proprietary - all rights reserved)
└── README.md

```

## 🔒 License
Proprietary — All rights reserved.  
Copyright (c) 2025 David Lancaster.
