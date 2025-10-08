"""
Utility script to clean up orphaned Redis keys.
Run this to remove sync tokens for databases that no longer exist.
"""
import os
import redis
from pathlib import Path

def clean_redis():
    """Remove orphaned sync tokens from Redis."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.Redis.from_url(redis_url, decode_responses=True)
    
    # Get all database files
    db_dir = Path("databases")
    existing_dbs = {f.stem for f in db_dir.glob("*.json")} if db_dir.exists() else set()
    
    print(f"Existing databases: {existing_dbs}")
    
    # Get all sync tokens
    sync_tokens = r.keys("tdms:sync:token:*")
    print(f"\nFound {len(sync_tokens)} sync tokens in Redis")
    
    # Clean up orphaned tokens
    orphaned = []
    for key in sync_tokens:
        db_name = key.replace("tdms:sync:token:", "")
        if db_name not in existing_dbs:
            orphaned.append(db_name)
            r.delete(f"tdms:sync:token:{db_name}")
            r.delete(f"tdms:sync:lock:{db_name}")
            r.delete(f"tdms:sync:last_sync:{db_name}")
            print(f"  ✓ Cleaned up orphaned sync for: {db_name}")
    
    if not orphaned:
        print("  ✓ No orphaned tokens found")
    else:
        print(f"\nCleaned up {len(orphaned)} orphaned sync tokens")
    
    # Show remaining keys
    all_keys = r.keys("tdms:*")
    print(f"\nRemaining Redis keys ({len(all_keys)}):")
    for key in sorted(all_keys):
        print(f"  - {key}")

if __name__ == "__main__":
    clean_redis()

