from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


# Serve CSS, JavaScript, and other static files
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# Serve the MiniTeams frontend
@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")
# Health Check
@app.get("/health")
def health():
    return {"status": "ok"}