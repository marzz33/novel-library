from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class FineStatus(Enum):
    PAID = "Paid"
    UNPAID = "Unpaid"
    WAIVED = "Waived"

class Fine(db.Model):

    __tablename__ = "Fines"

    id                   = db.Column(db.Integer, primary_key=True)
    fine_id              = db.Column(db.String(45), unique=True, nullable=False)
    transaction_id       = db.Column(db.String(45), db.ForeignKey("Transactions.transaction_id"), nullable=False)
    user_id              = db.Column(db.String(45), db.ForeignKey("users.user_id"), nullable=False)
    amount               = db.Column(db.Float, nullable=False)
    issued_on            = db.Column(db.DateTime, default=utcnow)
    status               = db.Column(db.Enum(FineStatus), nullable=False, default=FineStatus.UNPAID)
    resolved_on          = db.Column(db.DateTime, nullable=True)
    reason               = db.Column(db.String(320), nullable=False)

    # Added these relationships to allow for easier access to user and transaction details when viewing fines,
    # it will also allow for easier querying of fines by user or transaction in the future if needed
    user                 = db.relationship("User", backref="fines")
    transaction          = db.relationship("Transaction", backref="fines")

    def __init__(self, user_id: str, transaction_id: str, reason: str, amount: float = 0.0):
        self.fine_id         = str(uuid.uuid4())
        self.transaction_id  = transaction_id
        self.user_id         = user_id
        self.amount          = amount
        self.issued_on        = utcnow()
        self.status           = FineStatus.UNPAID
        self.resolved_on      = None
        self.reason           = reason

    # Member uses this function to pay their fine, it will also check if the fine has
    # already been paid or waived before allowing the user to pay
    def paid(self):
        if self.status == FineStatus.WAIVED:
            raise ValueError("Fine has already been waived.")
        elif self.status == FineStatus.PAID:
            raise ValueError("Fine has already been paid.")
        self.status = FineStatus.PAID
        self.resolved_on = utcnow()
        db.session.commit()

    # Admin uses this function to waive a fine, it will also check if the fine has already been paid
    # or waived before allowing the admin to waive the fine
    def waive(self):
        if self.status == FineStatus.PAID:
            raise ValueError("Fine has already been paid and cannot be waived.")
        elif self.status == FineStatus.WAIVED:
            raise ValueError("Fine has already been waived.")
        
        self.status = FineStatus.WAIVED
        self.resolved_on = utcnow()
        db.session.commit()

    def get_status(self):
        return self.status
    
    @staticmethod
    def get_unpaid_fines(user_id): 
        return Fine.query.filter_by(user_id = user_id, status = FineStatus.UNPAID).all()
    
    def calculate_fine(self):

        transaction = self.transaction
        if transaction is None or transaction.due_date is None:
            return 0.0
        
        overdue_days = (utcnow() - transaction.due_date).days
        if overdue_days <= 0:
            return 0.0
        
        rate = 10.0 if transaction.item_type == "Computer" else 1.0
        return  round(rate * overdue_days, 2)
    
    # Allows members to view their fines with basic details, it will also allow admins to
    # view fines with basic details when viewing a user's profile
    def member_dict(self):
        return {
            "fine_id": self.fine_id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "issued_on": self.issued_on.isoformat(),
            "reason": self.reason,
            "status": self.status.value,
            "resolved_on": self.resolved_on.isoformat() if self.resolved_on else None
        }
    
    # Allows admins to view fines with full details when viewing a transaction or when viewing
    # all fines in the system, it will include user and item details for the transaction associated with the fine
    def get_full_details(self):
        transaction1 = self.transaction

        # Prevents a crash in the unlikely event that a fine is created for a transaction that doesn't exist/deleted,
        # it will just return None for the item title in this case instead of crashing the system
        item = transaction1.item if transaction1 else None

        return {
            "fine_id": self.fine_id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "item_title": item.title if item else None,
            "amount": self.amount,
            "issued_on": self.issued_on.isoformat(),
            "reason": self.reason,
            "status": self.status.value,
            "resolved_on": self.resolved_on.isoformat() if self.resolved_on else None
        }