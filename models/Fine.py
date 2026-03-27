from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid
from models.Items import Item
from models.users import User

def utcnow():
    return datetime.now(timezone.utc)

