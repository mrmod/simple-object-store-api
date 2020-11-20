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

# Data Model

S3 is used as the guiding principle for the model which extends what is in Redis with:

## Accounts

```
# An Account DisplayName
/accounts/$ACCOUNT_ID/name "Larry Purdesh"

# Accounts have many buckets
/accounts/$ACCOUNT_ID/buckets {Bucket1, Bucket2}
```

## Bucket

```
# A Set of buckets for an account
/accounts/$ACCOUNT_ID/buckets {Bucket1, Bucket2}

# A CreationDate
/accounts/$ACCOUNT_ID/buckets/$BUCKET/creationDate  "2020-11-20 09:03:20.903719"

# Buckets have many keys
/keys/$ACCOUNT_ID/$BUCKET {Key1, Key2}
```

## Key

```
# A Set of keys for a bucket
/keys/$ACCOUNT_ID/$BUCKET {Key1, Key2}

# A Set of objects for a key
/keys/$ACCOUNT_ID/$BUCKET/$KEY {ObjectID1, ObjectID2}

# Size of a key
/keys/$ACCOUNT_ID/$BUCKET/$KEY/size 1000
```


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