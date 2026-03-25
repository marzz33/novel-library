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

    __tablename__ = "Items"

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

    def __init__(self, title: str, description: str, qty: int, item_type: str):
        
        self._item_id       = str(uuid.uuid4())
        self._title         = title
        self._description   = description
        self._qty           = qty
        self._available_qty = qty
        self.added_on       = utcnow()
        self._item_type     = item_type

    def check_availability(self):
        return self.available_qty > 0
    
    def get_details(self):
        return {
            "item_id": self.item_id,
            "title": self.title,
            "description": self.description,
            "qty": self.qty,
            "available_qty": self.available_qty,
            "added_on": self.added_on.isoformat(),
            "item_type": self.item_type
        }
    
    def loan(self, user_id):
        if not self.check_availability():
            raise Exception(f"{self.title} is not available for loan. Please make a reservation.")
        self.available_qty -= 1
        db.session.commit()
        # Needs to return a transaction record for the loan to be tracked and returned later