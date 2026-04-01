from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class NotificationType(Enum):
    DUE_SOON = "Due Soon"
    OVERDUE = "Overdue"
    RESERVATION_READY = "Reservation Ready"
    ACCOUNT_UPDATE = "Account Update"

class Notification(db.Model):

    __tablename__ = "Notifications"

    id                   = db.Column(db.Integer, primary_key=True)
    notification_id      = db.Column(db.String(45), unique=True, nullable=False)
    user_id              = db.Column(db.String(45), db.ForeignKey("Users.user_id"), nullable=False)
    type                 = db.Column(db.Enum(NotificationType), nullable=False)
    message              = db.Column(db.String(320), nullable=False)
    sent_on              = db.Column(db.DateTime, default=utcnow)
    is_read              = db.Column(db.Boolean, default=False)

    user                = db.relationship("User", backref="notifications")

    def __init__(self, user_id: str, notification_type: NotificationType, message: str):
        self.notification_id   = str(uuid.uuid4())
        self.user_id           = user_id
        self.type              = notification_type
        self.message           = message
        self.sent_on           = utcnow()
        self.is_read            = False

    # Allows the system to send a notification to a user, it will add the
    # notification to the database and commit the changes
    def send(self):
        db.session.add(self)
        db.session.commit()
    
    # Allows users to mark notifications as read
    def mark_as_read(self):
        self.is_read = True
        db.session.commit()

    # Allows users to delete notifications
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    # Allows users to view their notifications with basic details
    def to_dict(self):
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "notification_type": self.type.value,
            "message": self.message,
            "sent_on": self.sent_on.isoformat(),
            "is_read": self.is_read
        }

# -------------------- Helper Functions --------------------- #

def notify_due_soon(user_id: str, item_title: str):
    notification = Notification(
        user_id=user_id,
        notification_type=NotificationType.DUE_SOON,
        message=f"Your loan for '{item_title}' is due soon. Please return or renew it to avoid fines."
    )
    notification.send()

def notify_overdue(user_id: str, item_title: str):
    notification = Notification(
        user_id=user_id,
        notification_type=NotificationType.OVERDUE,
        message=f"Your loan for '{item_title}' is overdue. Please return it as soon as possible to avoid additional fines."
    )
    notification.send()

def notify_reservation_ready(user_id: str, item_title: str):
    notification = Notification(
        user_id=user_id,
        notification_type=NotificationType.RESERVATION_READY,
        message=f"The item '{item_title}' you reserved is now available for pickup. Please pick it up within 3 days to avoid cancellation."
    )
    notification.send()

def notify_account_update(user_id: str, update_message: str):
    notification = Notification(
        user_id=user_id,
        notification_type=NotificationType.ACCOUNT_UPDATE,
        message=update_message
    )
    notification.send()
