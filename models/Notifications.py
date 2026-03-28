from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
    return datetime.now(timezone.utc)

