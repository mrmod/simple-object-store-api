from fastapi import FastAPI, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from typing import Optional
import socket
import os

import model
import object_store
import s3_api

api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 API
api.include_router(s3_api.api)
# Size of object tags in bytes
OBJECT_ID_SIZE = 8
SOS_DATAPUTTER_ROUTER=("localhost", 5001)
CONTENT_LENGTH_HEADER_SIZE = 8
@api.post("/")
async def object_create(
    bytestream: bytes = File(...),
    content_length: Optional[str] = Header(None),
    x_sos_content_type: Optional[str] = Header(None),
    ):
    print(f"ContentLength: {content_length} or {len(bytestream)}")
    print(f"ContentType: {x_sos_content_type}")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(SOS_DATAPUTTER_ROUTER)
    print(f"Sending {len(bytestream)} bytes")
    s.send(len(bytestream).to_bytes(CONTENT_LENGTH_HEADER_SIZE, 'big'))
    s.send(bytestream)
    print(f"Sent {len(bytestream)} bytes")
    object_id = s.recv(OBJECT_ID_SIZE)
    print(f"Created {object_id}")
    s.close()

    model.set_content_type(
        object_id.decode("utf-8"),
        x_sos_content_type,
    )
    return {
        "objectId": object_id,
    }

# END S3 API

@api.get("/api")
def index():
    return {
        "objects": model.list_objects(),
    }

@api.get("/api/{object_id}")
def object_index(object_id, query=None):
    return {
        "ticketCount": model.get_ticket_count(object_id),
        "nodes": model.get_object_nodes(object_id),
        "tickets": model.get_object_tickets(object_id),
        "size": model.get_object_size(object_id),
        "contentType": model.get_content_type(object_id),
    }

@api.get("/api/{object_id}/stream")
async def object_stream(object_id):
    return StreamingResponse(
        object_store.stream(object_id),
        headers={
            "Content-Disposition": f"attachment; filename={object_id}", # TODO: Support object names
            "Content-Type": "application/octet-stream", # TODO: Support mimetypes
        },
    )