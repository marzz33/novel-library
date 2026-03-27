from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid
from models.Items import Item
from models.users import User

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

    # Added these relationships to allow for easier access to user and item details when viewing transactions,
    # it will also allow for easier querying of transactions by user or item in the future if needed
    # Solves the issue with get_summary due to pylance alert due to no relationship found
    user                 = db.relationship("User", backref="transactions")
    item                 = db.relationship("Item", backref="transactions")

    def __init__(self, user_id: str, item_id: str, transaction_type: TransactionType, item_type: str):
        self._transaction_id      = str(uuid.uuid4())
        self._user_id             = user_id
        self._item_id             = item_id
        self._transaction_type    = transaction_type
        self._item_type           = item_type
        self.status               = TransactionStatus.ACTIVE
        self.date                 = utcnow()

        # This allows a transaction to close itself if it is a return transaction,
        # otherwise it will set the due date based on the item type
        if transaction_type == TransactionType.RETURNED:
            self.due_date = None
            self.returned_date = utcnow()
            self.status = TransactionStatus.COMPLETED
        else:
            self.status = TransactionStatus.ACTIVE
            self.returned_date = None

        # This sets the due date based on the item type,
        # it will be used for both loan and renewed transactions
        if item_type == "Book":
            self.due_date = self.date + timedelta(days=28)
        elif item_type == "Movie":
            self.due_date = self.date + timedelta(days=7)
        else:
            self.due_date = self.date + timedelta(days=140)

    # This method marks a transaction as completed when a return transaction is created,
    # it will also update the returned date and increase the available quantity of the item in inventory
    def completed(self):
        self.status = TransactionStatus.COMPLETED
        self.returned_date = utcnow()
        item = Item.query.filter_by(item_id=self.item_id).first()
        if item:
            item.available_qty += 1
            db.session.commit()

    # This method checks if a transaction is overdue, if it is it will update the status to overdue and return true, 
    # otherwise it will return false
    def overdue(self):
        if (self.status == TransactionStatus.ACTIVE and self.due_date is not None and self.due_date < utcnow()):
            self.status = TransactionStatus.OVERDUE
            db.session.commit()

            # Fine & Notification triggers will go here once they are created and implemented
            return True
        return False
    
    # Calculates how much a user owes in fines for an overdue transaction,
    # it will return 0 if the transaction is not overdue or if the due date is not set
    def calculate_fine(self):
        if self.status != TransactionStatus.OVERDUE or self.due_date is None:
            return 0.0
        
        overdue_days = (utcnow() - self.due_date).days
        if self.item_type == "Computer":
            fine_rate = 10.0
        else:
            fine_rate = 1.0
        return fine_rate * overdue_days

    def get_summary(self):
        item = Item.query.filter_by(item_id=self.item_id).first()
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "title": item.title if item else None,
            "transaction_type": self.transaction_type.value,
            "item_type": self.item_type,
            "date": self.date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "returned_date": self.returned_date.isoformat() if self.returned_date else None,
            "status": self.status.value,
            "overdue": self.status == TransactionStatus.OVERDUE,
            "late_fee": self.calculate_fine()
        }
    def get_full_details(self):
        return {
            "transaction_id": self.transaction_id,
            "user": {
                "user_id": self.user_id,
                "name": self.user.name if self.user else None,
                "email": self.user.email if self.user else None
            },
            "item": {
                "item_id": self.item_id,
                "title": self.item.title if self.item else None,
                "description": self.item.description if self.item else None,
                "item_type": self.item.item_type if self.item else None
            },
            "transaction_type": self.transaction_type.value,
            "item_type": self.item_type,
            "date": self.date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "returned_date": self.returned_date.isoformat() if self.returned_date else None,
            "status": self.status.value,
            "overdue": self.status == TransactionStatus.OVERDUE,
            "late_fee": self.calculate_fine()
        }