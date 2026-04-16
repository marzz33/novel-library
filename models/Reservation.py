from app import db
from enum import Enum
from datetime import datetime, timezone, timedelta
import uuid


def utcnow():
    return datetime.now(timezone.utc)


class ReservationStatus(Enum):
    PENDING   = "Pending"     # In queue, item unavailable
    READY     = "Ready"       # Item available, member notified
    CONFIRMED = "Confirmed"   # Converted to loan
    EXPIRED   = "Expired"     # Member didn't collect in time
    CANCELLED = "Cancelled"   # Member cancelled


class Reservation(db.Model):
    # Handles both reservations and waitlist in one model.
    __tablename__ = "Reservations"

    id             = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.String(45), unique=True, nullable=False)
    user_id        = db.Column(db.String(45), db.ForeignKey("users.user_id"), nullable=False)
    item_id        = db.Column(db.String(45), db.ForeignKey("Items.item_id"), nullable=False)
    position       = db.Column(db.Integer, nullable=False)
    reserved_on    = db.Column(db.DateTime, default=utcnow)
    ready_by       = db.Column(db.DateTime, nullable=True)
    status         = db.Column(db.Enum(ReservationStatus), nullable=False, default=ReservationStatus.PENDING)

    user = db.relationship("User", backref="reservations")
    item = db.relationship("Item", backref="reservations")

    def __init__(self, user_id: str, item_id: str):
        self.reservation_id = str(uuid.uuid4())
        self.user_id        = user_id
        self.item_id        = item_id
        self.reserved_on    = utcnow()
        self.status         = ReservationStatus.PENDING
        self.ready_by       = None

        # Assign next queue position for this item
        # Looks for the highest existing position and adds 1
        # If no one is in the queue yet, position starts at 1
        last = Reservation.query.filter_by(
            item_id=item_id
        ).filter(
            db.or_(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.status == ReservationStatus.READY
            )
        ).order_by(db.desc(Reservation.position)).first()

        self.position = (last.position + 1) if last else 1

    # Called when an item is returned and this member is next in line
    # Gives members 3 days to pick up their reserved item before the reservation expires
    def mark_ready(self):
        from models.Notifications import notify_reservation_ready
        self.status   = ReservationStatus.READY
        self.ready_by = utcnow() + timedelta(days=3)
        db.session.commit()
        notify_reservation_ready(
            user_id    = self.user_id,
            item_title = self.item.title if self.item else "Your reserved item"
        )

    # Called when the member comes to pickup their reserved item
    # Creates a loan Transaction and marks this reservation as confirmed
    def convert_to_loan(self):
        from models.Transaction import Transaction, TransactionType
        from models.Items import Item

        if self.status not in (ReservationStatus.READY, ReservationStatus.CONFIRMED):
            raise ValueError("Item is not ready for collection yet.")

        if self.is_expired():
            raise ValueError("This reservation has expired.")

        # Query directly so Pylance knows the exact type
        item: Item | None = Item.query.filter_by(item_id=self.item_id).first()
        if item is None:
            raise ValueError("Item no longer exists.")

        item.available_qty -= 1

        txn = Transaction(
            user_id          = self.user_id,
            item_id          = self.item_id,
            transaction_type = TransactionType.LOAN,
            item_type        = item.item_type
        )
        self.status = ReservationStatus.CONFIRMED
        db.session.add(txn)
        db.session.commit()
        return txn

    # Called when the member cancels their spot in the queue/reservation.
    # Reorders the queue and notifies the next person if item is available
    def cancel(self):
        if self.status == ReservationStatus.EXPIRED:
            raise ValueError("Unable to cancel. Reservation has expired.")
        elif self.status == ReservationStatus.CANCELLED:
            raise ValueError("Reservation is already cancelled.")
        else:
            self.status = ReservationStatus.CANCELLED

        # Shift everyone behind this position up by 1
        # filter_by() is used to get only reservations for a specific item
        # db.or_() is used to filter for both PENDING and READY statuses, since both are active in the queue
        # all() is used to get the full list of affected reservations so we can loop through them and update their positions
        queue = Reservation.query.filter_by(
            item_id=self.item_id
        ).filter(
            db.or_(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.status == ReservationStatus.READY
            ),
            Reservation.position > self.position #type: ignore
        ).order_by(db.desc(Reservation.position)).all()

        for entry in queue:
            entry.position -= 1

        db.session.commit()

        # If item is available after cancellation, notify next in line
        from models.Items import Item
        item: Item | None = Item.query.filter_by(item_id=self.item_id).first()
        if item and item.check_availability():
            Reservation.notify_next(self.item_id)

    # Checks if the 3 day pick up window has passed
    # If it has, the queue is reordered and the next person is notified
    def is_expired(self) -> bool:
        if (self.status == ReservationStatus.READY
                and self.ready_by is not None
                and self.ready_by < utcnow()):

            self.status = ReservationStatus.EXPIRED

            # Shift everyone behind this position up by 1
            queue = Reservation.query.filter_by(
                item_id=self.item_id
            ).filter(
                db.or_(
                    Reservation.status == ReservationStatus.PENDING,
                    Reservation.status == ReservationStatus.READY
                ),
                Reservation.position > self.position #type: ignore
            ).order_by(db.desc(Reservation.position)).all()

            for entry in queue:
                entry.position -= 1

            db.session.commit()
            Reservation.notify_next(self.item_id)
            return True
        return False

    # Static method works on the whole Reservations table without needing access to a specific reservation object.
    # It finds the next person in line for a specific item and marks their reservation as ready.

    @staticmethod
    def notify_next(item_id: str):

        # Finds the next PENDING reservation for this item and marks it READY.
        # Called automatically when an item is returned or a reservation expires.

        next_in_queue = Reservation.query.filter_by(
            item_id = item_id,
            status = ReservationStatus.PENDING
        ).order_by(db.asc(Reservation.position)).first()

        if next_in_queue:
            next_in_queue.mark_ready()

    @staticmethod
    def get_queue(item_id: str) -> list:

        # Returns the current active queue for an item in order.
        # Allows admin to see who is waiting/next in line if a member asks about an item.

        return Reservation.query.filter_by(
            item_id=item_id
        ).filter(
            db.or_(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.status == ReservationStatus.READY
            )
        ).order_by(db.asc(Reservation.position)).all()

    @staticmethod
    def get_position(item_id: str, user_id: str) -> int:

        # Returns the member's current position in the queue.
        # Returns -1 if the member is not in the queue.

        entry = Reservation.query.filter_by(
            item_id=item_id,
            user_id=user_id
        ).filter(
            db.or_(
                Reservation.status == ReservationStatus.PENDING,
                Reservation.status == ReservationStatus.READY
            )
        ).first()
        return entry.position if entry else -1

    @staticmethod
    def is_empty(item_id: str) -> bool:

        # Returns True if no one is waiting for this item(no reservations in PENDING or READY status), False if there are active reservations.
        # Will be used in Transaction file when Transaction.completed() is called after a return.

        return Reservation.query.filter_by(
            item_id=item_id,
            status=ReservationStatus.PENDING
        ).count() == 0

    # Returns reservation details as a dictionary
    # Used in routes to send data back as JSON
    def get_details(self) -> dict:
        return {
            "reservation_id": self.reservation_id,
            "item_id":        self.item_id,
            "item_title":     self.item.title if self.item else None,
            "position":       self.position,
            "reserved_on":    self.reserved_on.isoformat(),
            "ready_by":       self.ready_by.isoformat() if self.ready_by else None,
            "status":         self.status.value
        }