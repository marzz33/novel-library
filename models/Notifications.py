from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class NotificationType(Enum):
    DUE_SOON = "Due Soon"
    OVERDUE = "Overdue"
    ITEM_RESERVED = "Item Reserved"
    WAITLISTED_ITEM = "Waitlisted Item"
    FINE_ISSUED = "Fine Issued"
    FINE_PAID = "Fine Paid"
    ACCOUNT_UPDATE = "Account Update"

class Notification(db.Model):

    __tablename__ = "Notifications"

    id                   = db.Column(db.Integer, primary_key=True)
    notification_id      = db.Column(db.String(45), unique=True, nullable=False)
    user_id              = db.Column(db.String(45), db.ForeignKey("Users.user_id"), nullable=False)
    notification_type    = db.Column(db.Enum(NotificationType), nullable=False)
    message              = db.Column(db.String(320), nullable=False)
    sent_on              = db.Column(db.DateTime, default=utcnow)
    is_read              = db.Column(db.Boolean, default=False)

    user                 = db.relationship("User", backref="notifications")

    def __init__(self, user_id: str, notification_type: NotificationType, message: str):
        self._notification_id   = str(uuid.uuid4())
        self._user_id           = user_id
        self._notification_type = notification_type
        self._message           = message
        self._sent_on           = utcnow()
        self.is_read            = False
    