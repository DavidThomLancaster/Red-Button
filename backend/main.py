# main.py
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# your routers
from router import handlers

# repos/services you already have
from Repositories.UserRepository import UserRepository
from Repositories.JobRepository import JobRepository
from Repositories.PromptRepository import PromptRepository
from Repositories.ContactRepository import ContactRepository
from Repositories.EmailRepository import EmailRepository
# (optional) your new EmailRepository


from FileManager.FileManager import FileManager
from Services.ContactService import ContactService
from Services.PromptService import PromptService
from Services.SchemaService import SchemaService
from Core.core import Core
from shared.StorageRef import StorageMode

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) one shared connection for the whole app
    conn = sqlite3.connect("app.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")

    # 2) repos share the SAME conn
    user_repo    = UserRepository(conn=conn)
    job_repo     = JobRepository(conn=conn)
    prompt_repo  = PromptRepository(conn=conn)
    contact_repo = ContactRepository(conn=conn)
    email_repo   = EmailRepository(conn=conn)  # uncomment when you add it

    # 3) shared services/singletons
    file_manager = FileManager(mode=StorageMode.LOCAL)
    contact_svc  = ContactService(contact_repo)
    prompt_svc   = PromptService(prompt_repo)
    schema_svc   = SchemaService()
    core         = Core(file_manager, contact_svc)

    # 4) stash on app.state for handlers/deps to reuse
    app.state.conn          = conn
    app.state.user_repo     = user_repo
    app.state.job_repo      = job_repo
    app.state.prompt_repo   = prompt_repo
    app.state.contact_repo  = contact_repo
    app.state.email_repo    = email_repo
    app.state.file_manager  = file_manager
    app.state.contact_svc   = contact_svc
    app.state.prompt_svc    = prompt_svc
    app.state.schema_svc    = schema_svc
    app.state.core          = core

    try:
        yield
    finally:
        try:
            conn.close()
        except Exception:
            pass

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routes
app.include_router(handlers.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001)#, reload=True) # reload got us into trouble last time! 



# from fastapi import FastAPI
# from router import handlers

# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# # Allow middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],  # dev frontend
#     allow_credentials=True,
#     allow_methods=["*"],   # includes OPTIONS
#     allow_headers=["*"],   # e.g., content-type, authorization
# )

# # include the routes
# app.include_router(handlers.router)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="127.0.0.1", port=8001)
