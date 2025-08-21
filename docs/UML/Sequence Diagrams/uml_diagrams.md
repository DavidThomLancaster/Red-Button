# 📐 UML Diagrams — Red Button (MVP)

This file contains **GitHub‑friendly Mermaid diagrams** that reflect the **current code** in `backend/router/handlers.py` and related services. Keep this as the editable source in `docs/uml/`. GitHub renders Mermaid inline — no image export needed. If you prefer PlantUML, you can mirror these in `.puml` files and (optionally) commit exported PNG/SVG alongside them.

> Last aligned with handlers that include: `/register`, `/login`, `/hello`, `/ping`, `/create_job`, `/get_job`, `GET /jobs/{job_id}`, `DELETE /jobs/{job_id}`, `POST /submit_pdf`, `GET|PATCH /jobs/{job_id}/contacts-map`.

---

## 1) Auth: Register & Login
```mermaid
sequenceDiagram
    autonumber
    actor U as User (Client)
    participant R as Router (FastAPI)
    participant US as UserService
    participant UR as UserRepository
    participant AU as AuthUtils
    participant TS as TokenService

    rect rgba(240,240,255,0.6)
    Note over U,R: POST /register { email, password }
    U->>R: RegisterRequest
    R->>US: register_user(email, password)
    US->>UR: find_by_email(email)
    UR-->>US: user? (none)
    US->>AU: hash_password(password)
    AU-->>US: password_hash
    US->>UR: create_user(email, password_hash)
    UR-->>US: user_id
    US-->>R: { user_id }
    R-->>U: 200 Created
    end

    rect rgba(240,255,240,0.6)
    Note over U,R: POST /login { email, password }
    U->>R: LoginRequest
    R->>US: login(email, password)
    US->>UR: find_by_email(email)
    UR-->>US: user (email, password_hash)
    US->>AU: verify_password(password, password_hash)
    AU-->>US: ok
    US->>TS: create_token(user_id)
    TS-->>US: access_token
    US-->>R: { access_token, token_type }
    R-->>U: 200 OK
    end
```

---

## 2) Jobs: Create / List / Detail / Delete
```mermaid
sequenceDiagram
    autonumber
    actor U as User (Client)
    participant R as Router
    participant AU as AuthUtils
    participant JS as JobService
    participant JR as JobRepository

    Note over U,R: POST /create_job { name, notes? } (Authorization: Bearer)
    U->>R: Request + Authorization
    R->>AU: get_user_id_from_header(Authorization)
    AU-->>R: user_id
    R->>JS: create_job(user_id, name, notes)
    JS->>JR: insert_new_job(...)
    JR-->>JS: job_id
    JS-->>R: { job_id }
    R-->>U: 200 OK

    Note over U,R: GET /get_job (list jobs)
    U->>R: Authorization
    R->>AU: get_user_id_from_header
    AU-->>R: user_id
    R->>JS: get_jobs(user_id)
    JS->>JR: find_by_user(user_id)
    JR-->>JS: jobs[]
    JS-->>R: { jobs }
    R-->>U: 200 OK

    Note over U,R: GET /jobs/{job_id}
    U->>R: Authorization + job_id
    R->>AU: get_user_id_from_header
    AU-->>R: user_id
    R->>JS: get_job_by_id(user_id, job_id)
    JS->>JR: find_by_id(job_id)
    JR-->>JS: job or null
    JS-->>R: { job } or 404
    R-->>U: 200 or 404

    Note over U,R: DELETE /jobs/{job_id}
    U->>R: Authorization + job_id
    R->>AU: get_user_id_from_header
    AU-->>R: user_id
    R->>JS: delete_job(user_id, job_id)
    JS->>JR: delete_if_owner(user_id, job_id)
    JR-->>JS: deleted?
    JS-->>R: { status: "DELETED" }
    R-->>U: 200 OK (or 404/403)
```

---

## 3) PDF Pipeline: `/submit_pdf`
```mermaid
sequenceDiagram
    autonumber
    actor U as User (Client)
    participant R as Router
    participant AU as AuthUtils
    participant JS as JobService
    participant FM as FileManager
    participant C as Core (LLM pipeline)
    participant PS as PromptService
    participant SS as SchemaService
    participant CS as ContactService
    participant JR as JobRepository

    Note over U,R: POST /submit_pdf (multipart: job_id, pdf_file)
    U->>R: Authorization + job_id + pdf_file
    R->>AU: get_user_id_from_header
    AU-->>R: user_id
    R->>JS: submit_pdf(user_id, job_id, pdf_bytes, safe_name)

    JS->>FM: save_pdf(user_id, job_id, pdf_bytes, safe_name)
    FM-->>JS: pdf_ref
    JS->>JR: update_status_pdf_saved(job_id, pdf_ref)

    JS->>C: extract_images(pdf_ref)
    C->>FM: save_images(...)
    FM-->>C: images_ref
    C-->>JS: images_ref
    JS->>JR: update_status_images_extracted(job_id, images_ref)

    JS->>PS: get_active_prompt()
    PS-->>JS: prompt_ref/prompt_text

    JS->>C: submit_to_llm(images_ref, prompt_text)
    C-->>JS: csv_refs[]

    JS->>SS: combine_csvs_to_json(csv_refs)
    SS-->>JS: normalized_json_ref

    JS->>CS: (optional) resolve_contact_ids(trades)
    CS-->>JS: contactsById

    JS->>JR: update_contacts_map(job_id, normalized_json_ref)
    JR-->>JS: status CONTACT_MAP_READY

    JS-->>R: { status, pdf_ref, images_ref, contacts_map_ref, contacts_map? }
    R-->>U: 200 OK
```

---

## 4) Contacts Map: Get & Patch
```mermaid
sequenceDiagram
    autonumber
    actor U as User (Client)
    participant R as Router
    participant AU as AuthUtils
    participant JS as JobService
    participant FM as FileManager
    participant JR as JobRepository

    rect rgba(245,245,255,0.6)
    Note over U,R: GET /jobs/{job_id}/contacts-map
    U->>R: Authorization + job_id
    R->>AU: get_user_id_from_header
    AU-->>R: user_id
    R->>JS: get_contacts_map(user_id, job_id)
    JS->>JR: assert_owner(user_id, job_id); get_contacts_map_ref(job_id)
    JR-->>JS: contacts_map_ref
    JS->>FM: load_json(contacts_map_ref)
    FM-->>JS: map JSON
    JS-->>R: { status:"OK", job_id, ref, map, contactsById }
    R-->>U: 200 OK
    end

    rect rgba(245,255,245,0.6)
    Note over U,R: PATCH /jobs/{job_id}/contacts-map { base_ref, ops[] }
    U->>R: Authorization + job_id + body
    R->>AU: get_user_id_from_header
    AU-->>R: user_id
    R->>JS: apply_contacts_map_ops(user_id, job_id, base_ref, ops)
    JS->>JR: assert_owner(user_id, job_id)
    JS->>JR: get_contacts_map_ref(job_id)
    JR-->>JS: current_ref
    JS->>FM: load_json(current_ref)
    FM-->>JS: current_map
    JS->>JS: apply ops → new_map
    JS->>FM: save_json(new_map)
    FM-->>JS: new_ref
    JS->>JR: update_contacts_map_ref(job_id, new_ref)
    JR-->>JS: ok
    JS-->>R: { ref:new_ref, map:new_map }
    R-->>U: 200 OK
    end
```

---

## 5) Notes on Keeping Diagrams in Sync
- **Source of truth**: keep these Mermaid diagrams in `docs/uml/uml_diagrams.md`.
- When you add new endpoints or services, update the relevant sequence.
- If you prefer PlantUML, create sibling files like `submit_pdf.puml` with the same logic.
- Consider a tiny checklist in PRs: “Updated UML if flow changed?” ✅

