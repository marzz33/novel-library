from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class ReseravtionStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    EXPIRED = "Expired"
    CANCELED = "Canceled"

class Reservation(db.Model):
    
    __tablename__ = "Reservations"

    id                  = db.Column(db.Integer, primary_key=True)
    reservation_id       = db.Column(db.String(36), unique=True, nullable=False)
    user_id              = db.Column(db.String(36), db.ForeignKey("users.user_id"), nullable=False)
    item_id              = db.Column(db.String(36), db.ForeignKey("Items.item_id"), nullable=False)
    reserved_on          = db.Column(db.DateTime, default=utcnow)
    start_date            = db.Column(db.DateTime, nullable=False)
    status               = db.Column(db.Enum(ReseravtionStatus), default=ReseravtionStatus.PENDING)

    user                = db.relationship("User", backref="reservations")
    item                = db.relationship("Item", backref="reservations")

    def __init__(self, user_id: str, item_id: str):
        self.reservation_id   = str(uuid.uuid4())
        self.user_id          = user_id
        self.item_id          = item_id
        self.reserved_on      = utcnow()
        self.start_date       = None
        self.status           = ReseravtionStatus.PENDING

    # Allows admin to confirm a reservation, it gives the member 3 days to pick up the item before the reservation expires
    def confirm(self):
        if self.status != ReseravtionStatus.PENDING:
            raise ValueError("Only pending reservations can be confirmed. Make sure member submited a reservation request before confirming.")
        self.status = ReseravtionStatus.CONFIRMED
        self.start_date = utcnow() + timedelta(days=3)
        db.session.commit()

    # Allows both member and admin to cancel a reservation, which frees the reserved item and
    # changes the available qty 
    def cancel(self):
        if self.status == ReseravtionStatus.CANCELED:
            raise ValueError("Reservation is already canceled.")
        if self.status == ReseravtionStatus.EXPIRED:
            raise ValueError("Cannot cancel an expired reservation.")
        self.status = ReseravtionStatus.CANCELED
        db.session.commit()

    def is_expired(self):
        if self.status == ReseravtionStatus.CONFIRMED and self.start_date is not None and self.start_date < utcnow():
            self.status = ReseravtionStatus.EXPIRED
            db.session.commit()
            return True
        return False
    