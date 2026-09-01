from pathlib import Path
import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError, field_validator


app = FastAPI()

connected_clients: set[WebSocket] = set()
broadcast_lock = asyncio.Lock()

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


def load_messages():
    items = []
    query_options = {
        "KeyConditionExpression": Key("roomId").eq(ROOM_ID)
    }

    while True:
        response = messages_table.query(**query_options)
        items.extend(response.get("Items", []))

        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            return items

        query_options["ExclusiveStartKey"] = last_key


async def broadcast_message(message: dict):
    message_json = json.dumps(message)

    async with broadcast_lock:
        disconnected = []
        for client in tuple(connected_clients):
            try:
                await client.send_text(message_json)
            except Exception:
                disconnected.append(client)

        for client in disconnected:
            connected_clients.discard(client)

class Message(BaseModel):
    display_name: str = Field(min_length=1, max_length=30)
    message: str = Field(min_length=1, max_length=500)

    @field_validator("display_name", "message")
    @classmethod
    def reject_blank_values(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


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
async def health():
    try:
        await asyncio.to_thread(
            messages_table.meta.client.describe_table,
            TableName=DYNAMODB_TABLE_NAME
        )
    except (BotoCoreError, ClientError) as error:
        raise HTTPException(status_code=503, detail="DynamoDB unavailable") from error

    return {"status": "ok"}


# Return all messages
@app.get("/messages")
async def get_messages():
    items = await asyncio.to_thread(load_messages)

    return [
        {
            "display_name": item["sender"],
            "message": item["content"]
        }
        for item in items
    ]


# Create a new message
@app.post("/messages")
async def post_message(new_message: Message):
    message = await asyncio.to_thread(
        save_message,
        new_message.display_name,
        new_message.message
    )
    await broadcast_message(message)
    return message

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    connected_clients.add(websocket)

    try:
        while True:

            data = await websocket.receive_text()

            try:
                parsed_data = json.loads(data)
                validated_message = Message.model_validate(parsed_data)
            except (json.JSONDecodeError, ValidationError, TypeError):
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message payload"
                })
                continue

            message = await asyncio.to_thread(
                save_message,
                validated_message.display_name,
                validated_message.message
            )

            await broadcast_message(message)

    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)
