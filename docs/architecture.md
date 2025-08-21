# 🧱 System Architecture – Red Button

This document defines the architecture of **Red Button**, an AI-powered tool to automate subcontractor outreach for construction estimators.  
It is designed for modularity, clarity, and a path to production scalability.

---

## 🔭 Overview

Red Button processes uploaded construction plans to:

1. Extract relevant trades using AI (via OpenAI GPT models)  
2. Normalize trade names against a schema  
3. Match trades to contacts from a database  
4. Generate targeted solicitation emails  

The system is built as a **full-stack web application** with a modular backend, React frontend, and a pipeline-oriented architecture.

---

## 🤩 System Components

### 1. Frontend
- **React + Vite + TypeScript**  
- Handles user authentication, job creation, PDF upload, trade review, and email preview  
- Communicates with backend via REST API  

### 2. Backend API
- **FastAPI (Python 3.12)**  
- Provides endpoints for:
  - User authentication (`/login`, `/register`)  
  - Job creation, PDF upload, job status retrieval  
  - Contact CRUD operations  
  - Pipeline orchestration (PDF → images → AI → CSV → JSON → normalized JSON)  
- Orchestrates the AI pipeline and contact-matching flow  

### 3. Core Logic
- Stateless Python modules for:
  - PDF/image processing (**PyMuPDF / fitz**)  
  - AI interaction (**openai** client)  
  - Trade normalization  
  - Contact matching  
- Designed to be testable in isolation, independent of API layer  

### 4. Pipeline Orchestrator
- Drives full process:  
  `PDF → Images → LLM → CSV → Combined JSON → Normalized JSON → Contacts`  
- Reusable from CLI or API  

### 5. Email Engine
- Planned:  
  - Load templates and generate email content  
  - Send via SendGrid (or compatible service)  
  - Log success/failure per recipient  
- Currently in production  

### 6. Data Storage
- **MVP**: SQLite database (`jobs.db`)  
- **Planned**: PostgreSQL in production  
- Files stored locally in `backend/storage/`  
- Logs stored as flat files per job  

---

## 🥤 Data Flow: Job Lifecycle

```text
[User Uploads PDF via Frontend]
    ↓
[Backend saves PDF to storage + jobs.db record]
    ↓
[PDF split into images via PyMuPDF]
    ↓
[Images & prompt sent to OpenAI GPT model]
    ↓
[Raw trades returned as CSV]
    ↓
[CSV files combined into JSON]
    ↓
[Trade names normalized against schema]
    ↓
[Contacts matched to trades from DB]
    ↓
[Resulting JSON returned + saved for job]

```

## 🗂️ Repository Structure

```bash
redbutton/
├── backend/             # FastAPI app, core logic, services
│   ├── Core/            # Stateless logic (PDF, LLM, normalization, combine)
│   ├── FileManager/     # File storage abstraction
│   ├── Services/        # Job, contact, and pipeline orchestration
│   ├── router/          # FastAPI route handlers
│   ├── Utils/           # Logging, helpers
│   ├── jobs.db          # SQLite DB (ignored in GitHub)
│   └── main.py          # FastAPI entrypoint
│
├── frontend/            # React + Vite + TypeScript frontend
│   ├── src/             # Components, routes, hooks
│   ├── public/          # Static assets
│   └── vite.config.ts
│
├── docs/                # Planning and specifications
│   ├── architecture.md
│   ├── srs.md
│   ├── vertical_slices.md
│   ├── file_structure.md
│   └── uml/             # PlantUML diagrams
│
├── tests/               # Backend tests
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
├── .gitignore
├── LICENSE              # Proprietary license
└── README.md

```

## 📡 API Endpoints (MVP)
| Method | Endpoint                      | Auth | Status      | Body / Params                                             | Returns (200)                                           |
| -----: | ----------------------------- | :--: | ----------- | --------------------------------------------------------- | ------------------------------------------------------- |
|    GET | `/hello`                      |  No  | Implemented | —                                                         | `{ message }`                                           |
|    GET | `/ping`                       |  No  | Implemented | —                                                         | `{ status }`                                            |
|   POST | `/register`                   |  No  | Implemented | JSON `{ email, password }`                                | `{ message, user_id }`                                  |
|   POST | `/login`                      |  No  | Implemented | JSON `{ email, password }`                                | `{ access_token, token_type }`                          |
|   POST | `/create_job`                 |  Yes | Implemented | JSON `{ name, notes? }`                                   | `{ message, job_id }`                                   |
|    GET | `/get_job`                    |  Yes | Implemented | —                                                         | `{ jobs: [...] }`                                       |
|    GET | `/jobs/{job_id}`              |  Yes | Implemented | `job_id` path param                                       | `{ job }`                                               |
| DELETE | `/jobs/{job_id}`              |  Yes | Implemented | `job_id` path param                                       | `{ status: "DELETED", job_id }`                         |
|   POST | `/submit_pdf`                 |  Yes | Implemented | `multipart/form-data`: `job_id` (form), `pdf_file` (file) | LLM pipeline result (e.g., refs, status, contacts\_map) |
|    GET | `/jobs/{job_id}/contacts-map` |  Yes | Implemented | `job_id` path param                                       | `GetMapResp` (contacts map + refs)                      |
|  PATCH | `/jobs/{job_id}/contacts-map` |  Yes | Implemented | JSON `{ base_ref, ops: [...] }`                           | Updated map payload from `apply_contacts_map_ops`       |



---

## 🧠 Technical Details
- Languages: Python 3.12, TypeScript
- Frameworks: FastAPI, React (Vite)
- AI Provider: OpenAI GPT-4 API
- Email Service: SendGrid (planned)
- Database: SQLite (MVP), PostgreSQL (planned)
- Containerization: Docker + Docker Compose (planned)
- Env Management: .env files + python-dotenv

---

## 📄 Database Schema (MVP)

- `users (user_id, email [UNIQUE], password_hash, created_at)`
- `jobs (job_id, user_id, name, notes, status, pdf_ref, pdf_mode,images_ref, images_mode,prompt_ref, prompt_mode, csvs_ref, csvs_mode,
jsons_ref, jsons_mode,
current_mapped_contacts_ref,
schema_ref, schema_mode,
created_at)`
- `contacts (id, name, email, phone, service_area)`
- `contact_trades (contact_id, trade)`  <!-- mapping table for many-to-many contact↔trade -->
- `prompts (prompt_id, name, content, version, created_at, is_active)`
- `email_logs (id, job_id, contact_id, status, timestamp)` *(planned)*

> Notes:
> - Heavy artifacts (PDFs, images, CSV/JSON) are **not** stored in the DB; only string refs (e.g., `pdf_ref`) that point to files managed by the FileManager.
> - The old `files` table isn’t used in the current design (replaced by the storage‐ref fields on `jobs`).
> - Only one prompt is active at a time.



---
## 🧐 Design Choices & Risks

| Decision                   | Rationale                           | Risks / Tradeoffs                 |
| -------------------------- | ----------------------------------- | --------------------------------- |
| FastAPI over Django        | Lightweight, async, quick iteration | Less built-in tooling/admin       |
| SQLite for MVP             | Simplicity, no external services    | Limited concurrency; will migrate |
| GPT-4 for trade extraction | Powerful natural language ability   | Cost + latency variability        |
| Local file storage for MVP | Easy to implement                   | Not scalable; plan for S3/R2      |
| Proprietary repo           | Protects business IP                | Limits open-source contributions  |


---
##🚧 Error Handling Strategy

- Centralized logging (backend/Utils/logger.py)
- Try/catch wrappers for:
- LLM API errors (timeouts, malformed CSV/JSON)
- PDF/image extraction errors
- Contact matching with missing schema entries
- Errors logged per job in backend/storage/logs/
- Frontend displays summarized errors to user
---
## 🔒 Security Principles

- Auth required for all routes beyond login/register
- Uploaded files stored in user-specific directories
- Input validation + sanitization at API boundaries
- API keys and secrets loaded only from environment
- Planned rate limiting to prevent abuse
---
## 🚀 Deployment Plan

- Local development: uvicorn + Vite dev server
- Planned: Docker Compose with three services:
 - api → FastAPI backend
 - db → PostgreSQL
 - frontend → React build served via Nginx
- Future: Cloud deployment (Render, AWS, or equivalent)
---
##🔮 Future Considerations

- Stripe-based billing for SaaS tiers
- Multi-user teams and shared jobs
- Customizable AI prompts per job
- Email click/open tracking
- Migration to scalable file storage (S3/R2)