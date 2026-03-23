from datetime import datetime, timezone
from enum import Enum
from app import db
import uuid

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

