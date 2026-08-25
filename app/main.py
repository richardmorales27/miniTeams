from pathlib import Path
import json
import os
import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


app = FastAPI()

messages = []
connected_clients = []

ROOM_ID = "GENERAL"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "miniteams-messages")
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
messages_table = dynamodb.Table(DYNAMODB_TABLE_NAME)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

def save_message(display_name: str, content: str):
    created_at = datetime.now(timezone.utc).isoformat()

    message_id = f"{created_at}#{uuid.uuid4()}"

    item = {
        "roomId": ROOM_ID,
        "messageId": message_id,
        "sender": display_name,
        "content": content,
        "createdAt": created_at
    }

    messages_table.put_item(Item=item)

    return {
        "display_name": display_name,
        "message": content
    }

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
    response = messages_table.query(
        KeyConditionExpression=Key("roomId").eq(ROOM_ID)
    )

    items = response.get("Items", [])

    return [
        {
            "display_name": item["sender"],
            "message": item["content"]
        }
        for item in items
    ]


# Create a new message
@app.post("/messages")
def post_message(new_message: Message):
    return save_message(
        new_message.display_name,
        new_message.message
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    connected_clients.append(websocket)

    try:
        while True:

            data = await websocket.receive_text()

            parsed_data = json.loads(data)

            validated_message = Message(**parsed_data)

            message = save_message(
                validated_message.display_name,
                validated_message.message
            )

            message_json = json.dumps(message)

            for client in connected_clients:
                await client.send_text(message_json)

    except WebSocketDisconnect:
        connected_clients.remove(websocket)

