from subtitles.subs import SubsClient
from store.database import SessionLocal, engine


subs_client = None

def get_subs_client() -> SubsClient:
    global subs_client
    if subs_client is None:
        subs_client = SubsClient()
    return subs_client

# Dependency
def get_db() -> SessionLocal:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()