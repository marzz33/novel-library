from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
    return datetime.utcnow()  # type: ignore[deprecated]

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
    user_id              = db.Column(db.String(45), db.ForeignKey("users.user_id"), nullable=False)
    item_id              = db.Column(db.String(45), db.ForeignKey("Items.item_id"), nullable=False)
    transaction_type     = db.Column(db.Enum(TransactionType), nullable=False)
    
    # Added item_type again in the event we need to query transactions by item type without importing Items
    # while also allowing one to view a transaction incase it is removed from our inventory
    item_type            = db.Column(db.String(20), nullable=False)
    
    date                 = db.Column(db.DateTime, default=utcnow)
    due_date             = db.Column(db.DateTime, nullable=True)
    returned_date        = db.Column(db.DateTime, nullable=True)
    status               = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.ACTIVE)
    renewed_count        = db.Column(db.Integer, default = 0, nullable = False)
    max_renewals         = 1

    # Added these relationships to allow for easier access to user and item details when viewing transactions,
    # it will also allow for easier querying of transactions by user or item in the future if needed
    # Solves the issue with get_summary due to pylance alert due to no relationship found
    user                 = db.relationship("User", backref="transactions")
    item                 = db.relationship("Item", backref="transactions")

    def __init__(self, user_id: str, item_id: str, transaction_type: TransactionType, item_type: str, due_date: datetime | None = None):
        self.transaction_id      = str(uuid.uuid4())
        self.user_id             = user_id
        self.item_id             = item_id
        self.transaction_type    = transaction_type
        self.item_type           = item_type
        self.date                = utcnow()

        # This allows a transaction to close itself if it is a return transaction,
        # otherwise it will set the due date based on the item type
        if transaction_type == TransactionType.RETURNED:
            self.due_date = None
            self.returned_date = utcnow()
            self.status = TransactionStatus.COMPLETED
        else:
            self.returned_date = None
            self.status = TransactionStatus.ACTIVE

            # This allows us to overwrite the due date if provided, this is useful for renewals to set a a new due date
            if due_date is not None:
                self.due_date = due_date
            else:

                from models.Items import Item

                item = Item.query.filter_by(item_id = item_id).first()
                self.due_date = item.get_due_date() if item else utcnow() + timedelta(days = 7)

    # This method marks a transaction as completed when a return transaction is created,
    # it will also update the returned date and increase the available quantity of the item in inventory
    def completed(self):

        from models.Reservation import Reservation
        from models.Fine import Fine, FineStatus
        from models.Items import Item

        # This adds a guard and avoids having a transaction be marked completed multiple
        # times which could lead to inventory issues with available quantity not being updated correctly
        if self.status == TransactionStatus.COMPLETED:
            raise ValueError("Transaction is already completed.")

        self.status = TransactionStatus.COMPLETED
        self.returned_date = utcnow()

        # Creates fine if the item returned did not already have one
        if self.due_date and self.returned_date > self.due_date:
            self.create_fine()

        # This recalculates the fine amount in the event a user already has a fine from being marked overdue
        # this amount will be final
        fine = Fine.query.filter_by(transaction_id = self.transaction_id).first()
        if fine and fine.status == FineStatus.UNPAID:
            fine.amount = fine.calculate_fine()

        item = Item.query.filter_by(item_id = self.item_id).first()
        if item:
            item.available_qty += 1

        db.session.commit()

        if item and not Reservation.is_empty(self.item_id):
            Reservation.notify_next(self.item_id)

     # Transaction creates the initial fine record when a transaction becomes overdue, it will
    # check if a fine already exists for this transaction before creating a new one to avoid duplicates
    def create_fine(self):
        from models.Fine import Fine
        
        # Check if a fine already exists for this transaction and avoids having multiple
        check = Fine.query.filter_by(transaction_id = self.transaction_id).first()
        if check:
            return

        overdue_days = (utcnow() - self.due_date).days if self.due_date else 0
        rate = 10.0 if self.item_type == "Computer" else 1.0
        amount = round(rate * overdue_days, 2)

        # In the event an item is removed from inventory after a transaction is created, we still want to
        # create a fine with basic details instead of erroring out due to missing item details
        item_title = self.item.title if self.item else f"Item {self.item_id}"
        fine = Fine(
            user_id = self.user_id,
            transaction_id = self.transaction_id,
            reason = f"Overdue {self.item_type}: {item_title}",
            amount = amount
        )
        db.session.add(fine)
        db.session.commit()

    # This method checks if a transaction is overdue based on the current date and the due date, it also checks if the transaction is still active
    def is_overdue(self):
        return (self.status in (TransactionStatus.ACTIVE, TransactionStatus.OVERDUE) and self.due_date is not None and self.due_date < utcnow())
    
    # This method marks a transaction as overdue if it is past the due date, it will also create a fine for the overdue transaction
    def mark_overdue(self): 
        if self.status != TransactionStatus.ACTIVE:
            return False
        if not self.is_overdue():
            return False
        
        self.status = TransactionStatus.OVERDUE
        db.session.commit()
        self.create_fine()
        return True
    
    def renew(self):
        if self.status != TransactionStatus.ACTIVE:
            raise ValueError("Only active transactions can be renewed.")
        
        if self.renewed_count >= self.max_renewals:
            raise ValueError("Maximum number of renewals reached (1).")

        from models.Items import Item

        item = Item.query.filter_by(item_id = self.item_id).first()
        if item and not item.is_renewable():
            raise ValueError(f"{item.title} is not eligible for renewal.")
        
        from models.Reservation import Reservation
        if not Reservation.is_empty(self.item_id):
            raise ValueError("Cannot renew Item. There are pending reservations for this item.")

        # Extends the due date by the original loan period of the item, if item is not found it defaults to 7 days
        # This allows users to not use the remaining loan period if they renew early,
        # but also allows them to use the remaining loan period if they renew late but before it becomes overdue
        loan_days = item.loan_days if item else 7
        base_day = self.due_date if self.due_date and self.due_date > utcnow() else utcnow()
        new_due_date = base_day + timedelta(days = loan_days)

        # Marks the current transaction as completed, this allows us to keep a history of all transactions including renewals without having to update the original (mutated)
        self.status = TransactionStatus.COMPLETED
        self.returned_date = utcnow()
        self.renewed_count += 1

        # Creates a new transaction for the renewed item, this allows us to keep track of the new due date and any future renewals separately from the original transaction
        new_transaction = Transaction(
            user_id = self.user_id,
            item_id = self.item_id,
            transaction_type = TransactionType.RENEWED,
            item_type = self.item_type
        )
        new_transaction.due_date = new_due_date
        new_transaction.renewed_count = self.renewed_count

        db.session.add(new_transaction)
        db.session.commit()
        return new_transaction

    def get_summary(self):
        return {
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "title": self.item.title if self.item else None,
            "transaction_type": self.transaction_type.value,
            "item_type": self.item_type,
            "date": self.date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "returned_date": self.returned_date.isoformat() if self.returned_date else None,
            "status": self.status.value,
            "overdue": self.status == TransactionStatus.OVERDUE,
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
        }