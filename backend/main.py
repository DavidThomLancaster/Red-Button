from fastapi import FastAPI
from router import handlers

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # dev frontend
    allow_credentials=True,
    allow_methods=["*"],   # includes OPTIONS
    allow_headers=["*"],   # e.g., content-type, authorization
)

# include the routes
app.include_router(handlers.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001)
