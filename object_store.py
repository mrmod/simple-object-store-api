import socket
import os
from typing import List

OBJECT_ID_SIZE = 8
SOS_DATAPUTTER_ROUTER = (
    os.environ.get("SOS_DATAPUTTER_ROUTER_HOST") or "localhost",
    5001,
)
CONTENT_LENGTH_HEADER_SIZE = 8

# SimpleObjectStore server
SOS_OBJECT_SERVER = (
    "127.0.0.1",
    5004
)

# Stream 1500-bytes at a time of an object
# from data-putter to here
async def stream(object_id):
    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    s.connect(SOS_OBJECT_SERVER)
    s.send(object_id.encode())

    while True:
        chunk = s.recv(1500)
        if len(chunk) == 0:
            break
        yield chunk
    
    s.close()

async def put(data: List[bytes], content_length: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(SOS_DATAPUTTER_ROUTER)
        s.send(content_length.to_bytes(CONTENT_LENGTH_HEADER_SIZE, "big"),)
        s.send(data)

        object_id = s.recv(OBJECT_ID_SIZE)
    return object_id

DELETE_COMMAND = "0DEL0DEL"
DELETE_AUTHENTICITY_TOKEN = "ABadSharedToken!"
async def delete(object_id: str):
    print(f"Store.delete {object_id}")
    request = f"{DELETE_COMMAND}{object_id}{DELETE_AUTHENTICITY_TOKEN}"
    print(f"DataPutter delete request: {request}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(SOS_DATAPUTTER_ROUTER)
        s.send(request.encode())

        object_id = s.recv(OBJECT_ID_SIZE)
    return object_id