from fastapi import FastAPI, File, Header, Request, Response
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

s3 = FastAPI()
s3.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# S3 API
s3.include_router(s3_api.api)


@s3.exception_handler(s3_api.S3ApiException)
async def s3_api_exception_handler(req: Request, ex: s3_api.S3ApiException):
    return Response(ex.body, status_code=ex.status_code, headers=s3_api.XML_HEADERS)


# API for UI
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
        "contentType": model.get_content_type(object_id) or "text/plain",
    }


@api.get("/api/{object_id}/stream")
async def object_stream(object_id):
    return StreamingResponse(
        object_store.stream(object_id),
        headers={
            "Content-Disposition": f"attachment; filename={object_id}",  # TODO: Support object names
            "Content-Type": "application/octet-stream",  # TODO: Support mimetypes
        },
    )
