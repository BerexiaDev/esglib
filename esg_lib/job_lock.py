from datetime import datetime, timedelta

from pymongo.errors import DuplicateKeyError

from esg_lib.document import Document
from esg_lib.utils import generate_id


class JobLock(Document):
    """Single-row distributed lock per job key, reusable by any service. `_id` IS the
    lock key (Mongo's unique _id index is the mutex); `expires_at` (ISO string) lets a
    crashed holder self-heal. Lives in the calling service's own DB."""
    __TABLE__ = "job_locks"
    _id = None
    holder_id = None
    acquired_at = None
    expires_at = None


def acquire_lock(key, ttl_seconds=3600):
    """Atomically claim `key` if free or expired. Returns a holder_id on success, else None."""
    now = datetime.utcnow()
    now_iso = now.isoformat()
    holder = generate_id()
    update = {"$set": {
        "holder_id": holder,
        "acquired_at": now_iso,
        "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(),
    }}
    try:
        doc = JobLock().find_one_and_update(
            {"_id": key, "$or": [{"expires_at": {"$lte": now_iso}}, {"expires_at": {"$exists": False}}]},
            update,
            upsert=True,
        )
    except DuplicateKeyError:
        return None  # another claimant holds the unexpired lock
    return holder if doc and doc.get("holder_id") == holder else None


def release_lock(key, holder_id):
    """Release only if still held by holder_id (never steal another holder's lock)."""
    JobLock.delete_all({"_id": key, "holder_id": holder_id})
