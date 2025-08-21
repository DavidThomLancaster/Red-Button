# 📋 Red Button — Requirements (MVP)

This document outlines the functional and non‑functional requirements for the Red Button project. It is intended as a lightweight Software Requirements Specification (SRS) to support development, testing, and future extension.

---

## 🎯 System Goals

* Automate subcontractor outreach for construction estimators.
* Process uploaded **construction plan PDFs** → extract relevant trades/notes → map to user’s contacts.
* Provide a simple web interface + backend API.
* Support sending customized emails to mapped contacts (planned).

---

## ✅ Functional Requirements

### Authentication & Users

* **Register**: Users can create an account with email + password.
* **Login**: Users can authenticate and receive a bearer token.
* **Authorization**: All job- and contact‑related endpoints require a valid token.

### Job Management

* **Create Job**: Users can create new jobs with name + optional notes.
* **List Jobs**: Users can retrieve all their jobs.
* **Get Job Details**: Users can fetch details of a specific job.
* **Delete Job**: Users can delete their own jobs.

### PDF Processing Pipeline

* **Submit PDF**: Users can upload a PDF to a job.

  * System stores PDF reference.
  * Extract images from PDF pages.
  * Send images + prompt to LLM core.
  * Collect CSV outputs and normalize into a structured JSON.
  * Update job status (`CONTACT_MAP_READY`).
* **Contacts Map**:

  * Retrieve the generated contacts map for a job.
  * Apply patch operations (`PATCH`) to update contacts map, producing a new version.

### Contacts (Planned)

* **CRUD**: Users can create, read, update, and delete their personal contact records.
* **Trade Tags**: Contacts can be tagged with one or more trade categories.

### Email Outreach (Planned)

* **Generate & Send Emails**: User can send customized emails to mapped contacts.
* **Email Logs**: System records delivery status for each email.

---

## 🔒 Non‑Functional Requirements

* **Security**: JWT bearer authentication; password hashing using secure algorithm (bcrypt/argon2).
* **Scalability**: MVP runs on SQLite + local file storage; must be portable to Postgres + S3.
* **Reliability**: API returns clear error messages with proper HTTP codes.
* **Maintainability**: Clear separation of concerns (Services, Repositories, FileManager, Core).
* **Portability**: Should run locally with `uvicorn` for dev; deployable to container/cloud.
* **Performance**: Handle PDFs up to \~25 MB and extract hundreds of pages without timeout (batch processing supported).

---

## 📌 Constraints & Assumptions

* **Assumption**: MVP will be used by a small number of estimators (single‑tenant per user account).
* **Constraint**: Initial deployment is local; no multi‑region or distributed storage until needed.
* **Constraint**: MVP email sending will rely on a simple SMTP or transactional email API (e.g., SendGrid).

---

## 🚀 Future Enhancements

* Multi‑tenant support for teams.
* Background job queue for heavy PDF/LLM processing.
* Contact deduplication and enrichment (company lookup).
* Advanced email campaign features (templates, scheduling, analytics).
* Role‑based permissions (admin vs estimator users).
