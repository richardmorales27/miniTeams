from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


app = FastAPI()

messages = []
connected_clients = []

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class Message(BaseModel):
    display_name: str
    message: str


# Serve CSS, JavaScript, and other static files
app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# Serve frontend
@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


# Health check
@app.get("/health")
def health():
    return {"status": "ok"}


# Return all messages
@app.get("/messages")
def get_messages():
    return messages


# Create a new message
@app.post("/messages")
def post_message(new_message: Message):
    message = {
        "display_name": new_message.display_name,
        "message": new_message.message
    }

    messages.append(message)

    return message

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    connected_clients.append(websocket)

    while True:
        data = await websocket.receive_text()
