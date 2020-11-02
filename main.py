from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import model
import object_store

api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/")
def index():
    return {
        "objects": model.list_objects(),
    }

@api.get("/{object_id}")
def object_index(object_id, query=None):
    return {
        "ticketCount": model.get_ticket_count(object_id),
        "nodes": model.get_object_nodes(object_id),
        "tickets": model.get_object_tickets(object_id),
        "size": model.get_object_size(object_id),
    }

@api.get("/{object_id}/stream")
async def object_stream(object_id):
    return StreamingResponse(
        object_store.stream(object_id),
        headers={
            "Content-Disposition": f"attachment; filename={object_id}", # TODO: Support object names
            "Content-Type": "application/octet-stream", # TODO: Support mimetypes
        },
    )