import socket

# SimpleObjectStore server
SOS_OBJECT_SERVER = (
    "127.0.0.1",
    5004
)

# Stream 1500-bytes at a time of an object
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
