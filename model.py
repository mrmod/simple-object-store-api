from redis import Redis
from typing import List
from datetime import datetime

redis = Redis(
    host="127.0.0.1",
    port=6379,
)

def list_objects():
    return redis.smembers("objects")

def get_ticket_count(object_id):
    return redis.get(f"/objects/{object_id}/ticketCounter")

def get_object_size(object_id):
    return redis.get(f"/objects/{object_id}/size")

def get_object_tickets(object_id):
    return redis.smembers(f"objectTickets/{object_id}")

def get_object_nodes(object_id):
    return redis.smembers(f"objectNodes/{object_id}")

def set_content_type(object_id, content_type):
    return redis.set(f"/objects/{object_id}/contentType", content_type)

def get_content_type(object_id):
    return redis.get(f"/objects/{object_id}/contentType").decode("UTF-8")

# Add a bucket to the set of buckets owned by ACCOUNT_ID
def create_bucket(bucket, account_id):
    # Every authorized entity can have buckets
    # Authorized entities often are members of groups
    key = f"/accounts/{account_id}/buckets"
    return redis.sadd(key, bucket)

def set_bucket_creation_date(bucket, account_id):
    key = f"/buckets/{account_id}/{bucket}/creationDate"
    creation_date = str(datetime.now())
    print(f"Creation date of {bucket}: {creation_date}")
    return redis.set(key, creation_date)

def get_bucket_creation_date(bucket, account_id):
    key = f"/buckets/{account_id}/{bucket}/creationDate"
    return redis.get(key).decode("UTF-8")

def list_bucket_names(account_id):
    key = f"/accounts/{account_id}/buckets"
    return [v.decode("UTF-8") for v in redis.smembers(key)]

def list_buckets(account_id):
    buckets = []
    for bucket_name in list_bucket_names(account_id):
        buckets.append({
            "name": bucket_name,
            "creation_date": get_bucket_creation_date(
                bucket_name,
                account_id,
            )
        })
    return buckets

def is_existing_bucket(bucket, account_id):
    key = f"/accounts/{account_id}/buckets"
    return redis.sismember(key, bucket)

def set_account_display_name(account_id):
    key = f"/accounts/{account_id}/name"
    return redis.set(key, account_id)

def get_account_display_name(account_id):
    key = f"/accounts/{account_id}/name"
    try: 
        return redis.get(key).decode("UTF-8")
    except AttributeError:
        set_account_display_name(account_id)
        return account_id

def get_bucket_owner(account_id):
    return {
        "display_name": get_account_display_name(account_id),
        "id": account_id,
    }

def set_key_size(bucket, key, size, account_id):
    size_key = f"/keys/{account_id}/{bucket}/{key}/size"
    return redis.set(size_key, size)

def get_key_size(bucket, key, account_id):
    key = f"/keys/{account_id}/{bucket}/{key}/size"
    return redis.get(key).decode("UTF-8")

# Add the key to the bucket
def add_key_to_bucket(bucket, key, account_id):
    prefix = f"/keys/{account_id}/{bucket}"
    return redis.sadd(prefix, key)

# Add objectID to a key
def add_object_to_key(bucket, key, object_id, account_id):
    prefix = f"/keys/{account_id}/{bucket}/{key}"
    return redis.sadd(prefix, object_id)

# List keys in a bucket
def list_bucket_keys(bucket, account_id):
    # TODO: Support prefix and delimiter
    prefix = f"/keys/{account_id}/{bucket}"
    return [v.decode("UTF-8") for v in redis.smembers(prefix)]

# ListObjectsv2
def get_bucket(bucket, account_id) -> List:
    bucket_keys = []
    display_name = get_account_display_name(account_id)

    for key in list_bucket_keys(bucket, account_id):
        bucket_keys.append({
            "display_name": display_name,
            "id": account_id,
            "size": get_key_size(bucket, key, account_id),
            "key": key,
        })
    return bucket_keys

def is_bucket_owner(bucket, account_id):
    key = f"/accounts/{account_id}/buckets"
    return redis.sismember(key, bucket) == 1

# Capability checks
def can_write_bucket(bucket, acount_id):
    return is_bucket_owner(bucket, account_id)
def can_read_bucket(bucket, account_id):
    return is_bucket_owner(bucket, account_id)
