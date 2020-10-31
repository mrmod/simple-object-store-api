from redis import Redis

redis = Redis(
    host="127.0.0.1",
    port=6379,
)

def list_objects():
    return redis.smembers("objects")

def get_ticket_count(object_id):
    print(f"TICKET COUNT FOR {object_id}")
    return redis.get(f"/objects/{object_id}/ticketCounter")

def get_object_size(object_id):
    return redis.get(f"/objects/{object_id}/size")

def get_object_tickets(object_id):
    return redis.smembers(f"objectTickets/{object_id}")

def get_object_nodes(object_id):
    return redis.smembers(f"objectNodes/{object_id}")