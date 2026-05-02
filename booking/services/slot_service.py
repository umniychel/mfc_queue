import redis

r = redis.Redis()


def lock_slot(slot_id):
    return r.set(f"slot_{slot_id}", "1", nx=True, ex=300)


def unlock_slot(slot_id):
    r.delete(f"slot_{slot_id}")