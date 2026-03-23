from datetime import datetime, timezone
from enum import Enum
from app import db
import uuid

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class MovieFormat(Enum):
    VHS = "VHS"
    DVD = "DVD"
    BLU_RAY = "Blu-ray"
    UHD = "4K UHD"

class Condition(Enum):
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"

class Item(db.Model):

    __tablename__ = "items"

    id                  = db.Column(db.Integer, primary_key=True)
    item_id             = db.Column(db.String(36), unique=True, nullable=False)
    title               = db.Column(db.String(200), nullable=False)
    description         = db.Column(db.String(300), nullable=True)
    qty                 = db.Column(db.Integer, nullable=False)
    available_qty       = db.Column(db.Integer, nullable=False)
    added_on            = db.Column(db.DateTime, default=utcnow)
    item_type           = db.Column(db.String(20), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': item_type,
        'polymorphic_identity': 'item'
    }
