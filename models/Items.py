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
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"

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
        self.item_id       = str(uuid.uuid4())
        self.title         = title
        self.description   = description
        self.qty           = qty
        self.available_qty = qty
        self.added_on      = utcnow()
        self.item_type     = item_type

    # Returns boolean indicating if the item is currently available for loan (available_qty > 0)
    def check_availability(self) -> bool:
        return self.available_qty > 0
    
    # Returns boolean indicating if the item can be renewed based on its type and any specific rules (e.g. max renewals, holds, etc.)
    # Base method returns False and can be overridden in subclasses for specific item types with their own renewal rules.
    def is_renewable(self):
        return False
    
    def get_type(self):
        return self.item_type
    
    # Returns item details as a dictionary, used in routes to send data back as JSON
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
    
    # Creates a loan Transaction for this item and decreases available quantity by 1
    def loan(self, user_id: str):

        from models.Transaction import Transaction, TransactionType

        if not self.check_availability():
            raise Exception(f"{self.title} is not available for loan. Please make a reservation.")
        
        self.available_qty -= 1
        transaction = Transaction(
            user_id=user_id,
            item_id=self.item_id,
            transaction_type=TransactionType.LOAN,
            item_type=self.item_type
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction
    
    def reserve(self, user_id: str):

        from models.Reservation import Reservation

        reservation = Reservation(
            user_id = user_id,
            item_id = self.item_id
        )
        db.session.add(reservation)
        db.session.commit()
        return reservation