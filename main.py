from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import model

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