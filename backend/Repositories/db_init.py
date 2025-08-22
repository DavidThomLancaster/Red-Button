# db_init.py
import sqlite3

from Repositories.UserRepository import UserRepository
from Repositories.JobRepository import JobRepository
from Repositories.ContactRepository import ContactRepository
from Repositories.PromptRepository import PromptRepository
#from Repositories.EmailRepository import EmailRepository  # you'll add this



# NOTE - This has been replaced by the set of in main.py. Delete this eventually. 
# TODO - eventually add the email repository once I know this works for the other repositories.
def init_repos(db_path: str = "app.db"):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # good SQLite settings for a web app
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")

    # IMPORTANT: pass the SAME conn to each repo
    user_repo = UserRepository(conn=conn)
    job_repo = JobRepository(conn=conn)
    contact_repo = ContactRepository(conn=conn)
    prompt_repo = PromptRepository(conn=conn)
    #email_repo = EmailRepository(conn=conn)  # new (below)

    return conn, user_repo, job_repo, contact_repo, prompt_repo, #email_repo
