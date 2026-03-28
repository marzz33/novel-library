from app import db
from datetime import datetime, timezone, timedelta
import json

def utcnow():
    return datetime.now(timezone.utc)

class Waitlist(db.Model):