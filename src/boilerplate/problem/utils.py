from datetime import datetime, timezone

def log(msg):
    print(f'{datetime.now(timezone.utc).isoformat()} {msg}')