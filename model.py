from redis import Redis
from typing import List

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
    return redis.get(f"/objects/{object_id}/contentType")

# Add a bucket to the set of buckets owned by ACCOUNT_ID
def create_bucket(bucket, account_id):
    # Every authorized entity can have buckets
    # Authorized entities often are members of groups
    key = f"/accounts/{account_id}/buckets"
    return redis.sadd(key, bucket)

def add_object_to_bucket(bucket, account_id, object_id):
    key = f"/buckets/{account_id}/{bucket}"
    return redis.sadd(key, object_id)

def get_bucket(bucket, account_id) -> List:
    key = f"/buckets/{account_id}/{bucket}"
    return redis.smembers(key)

def is_bucket_owner(bucket, account_id):
    key = f"/accounts/{account_id}/buckets"
    return redis.sismember(key) == 1

# Capability checks
def can_write_bucket(bucket, acount_id):
    return is_bucket_owner(bucket, account_id)
def can_read_bucket(bucket, account_id):
    return is_bucket_owner(bucket, account_id)
