# Simple Object Store HTTP API

An HTTP API to list and download objects from the [Simple Object Store](https://github.com/mrmod/data-putter) because asking for bytes is kinda needy.

# Getting Started

```
pip install -r requirements.txt

# Linux / Mac
./run-server.sh
# Windows
./run-server.bat
```

The server listens on port `8000` by default.

# API Documentation

Once the server has been started, docs are available at http://localhost:8000/docs

# Usage

With the API up, clients can create object store allocations using

```
curl -X POST http://$apiUrl -d @somefile
{
    "objectId": "Some Object ID",
}
```