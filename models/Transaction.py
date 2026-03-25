from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class TransactionType(Enum):
    LOAN = "Loan"
    RENEWED = "Renewed"
    RETURNED = "Returned"

class TransactionStatus(Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"

class Transaction(db.Model):

    __tablename__ = "Transactions"

    id                   = db.Column(db.Integer, primary_key=True)
    transaction_id       = db.Column(db.String(45), unique=True, nullable=False)
    user_id              = db.Column(db.String(45), db.ForeignKey("Users.user_id"), nullable=False)
    item_id              = db.Column(db.String(45), db.ForeignKey("Items.item_id"), nullable=False)
    transaction_type     = db.Column(db.Enum(TransactionType), nullable=False)
    status               = db.Column(db.Enum(TransactionStatus), nullable=False)
    
    # Added item_type again in the event we need to query transactions by item type without importing Items
    # while also allowing one to view a transaction incase it is removed from our inventory
    item_type            = db.Column(db.String(20), nullable=False)
    
    date                 = db.Column(db.DateTime, default=utcnow)
    due_date             = db.Column(db.DateTime, nullable=True)
    returned_date        = db.Column(db.DateTime, nullable=True)
    status               = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.ACTIVE)
    
    item = db.relationship("Item", backref="transactions")
    user = db.relationship("User", backref="transactions")    

    def __init__(self, user_id: str, item_id: str, transaction_type: TransactionType, item_type: str):
        self._transaction_id      = str(uuid.uuid4())
        self._user_id             = user_id
        self._item_id             = item_id
        self._transaction_type    = transaction_type
        self._item_type           = item_type
        self.status               = TransactionStatus.ACTIVE
        self.date                 = utcnow()

        if item_type == "book":
            self.due_date = self.date + timedelta(days=28)
        elif item_type == "movie":
            self.due_date = self.date + timedelta(days=7)
        elif item_type == "computer":
            self.due_date = self.date + timedelta(days=140)