from datetime import datetime, timezone
from enum import Enum
from typing import Any
from app import db, bcrypt
import uuid                                 # Generates new random ID for each user
from flask_login import UserMixin
from models.Transaction import Transaction
from models.Fine import Fine, FineStatus
from models.Reservation import Reservation




def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class UserRole(Enum):
    MEMBER = "Member"
    ADMIN  = "Admin"

class MemberStatus(Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"

# Abstract Base Class for Users
class User(UserMixin, db.Model):

    __tablename__ = "users"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.String(36), unique=True, nullable=False)
    name            = db.Column(db.String(80), nullable=False)
    email           = db.Column(db.String(150), unique=True, nullable=False)
    password        = db.Column(db.String(260), nullable=False)
    phone           = db.Column(db.String(20), nullable=True)
    added_on        = db.Column(db.DateTime, default=utcnow)
    role            = db.Column(db.Enum(UserRole), nullable=False)
    status          = db.Column(db.Enum(MemberStatus), nullable=True)
    
    # Added due to SQLAlchemy error
    # Keeps member from trying to add additional columns instead of inheriting from the User class
    member_since = db.Column(db.DateTime, nullable=  True)
    max_loanable_items = db.Column(db.Integer, nullable = True, default=4)
    max_loanable_computers = db.Column(db.Integer, nullable = True, default=1)
    
    permissions     = db.Column(db.JSON, nullable=True)

    __mapper_args__ = {
            'polymorphic_on':       role,
            'polymorphic_identity': UserRole.MEMBER
        }

    def __init__(self, user_id: str, name: str, email: str,
                 password: str, phone: str | None = None):
        self.user_id       = user_id
        self.name          = name
        self.email         = email
        self.password      = bcrypt.generate_password_hash(password).decode("utf-8")
        self.phone         = phone
        self.added_on      = utcnow()

    # This function allows us to check if the password provided by the user matches the hashed password stored in the database
    def check_password(self, password) -> bool:
        return bcrypt.check_password_hash(self.password, password)
    
    # This function is required by Flask-Login to get the unique identifier for the user, which in this case is the user_id
    def get_id(self):
        return self.user_id
    
    def get_role(self):
        return self.role
    
    def update_profile(self, name: str | None = None, email: str | None = None, phone: str | None = None):
        if name:
            self.name = name
        if email:
            self.email = email
        if phone:
            self.phone = phone
        db.session.commit()

    def get_notifications(self):
        from models.Notifications import Notification

        # Function retrieves all notifications for the user, ordered by the date they were sent in descending order (most recent)
        notifs = Notification.query.filter_by(user_id=self.user_id).order_by(db.desc(Notification.sent_on)).all()
        return notifs
    

class Member(User):

    __mapper_args__ = {
        'polymorphic_identity': UserRole.MEMBER
    }

    def __init__(self, name, email, password, phone= None):
        super().__init__(user_id = str(uuid.uuid4()), name = name, email = email, password = password, phone = phone)
        self.role = UserRole.MEMBER
        self.member_since = utcnow()
        self.status = MemberStatus.ACTIVE

    def check_loan_limits(self, item) -> bool:
        from models.Transaction import Transaction, TransactionType, TransactionStatus

        # Count active loans for the user
        active_loans = Transaction.query.filter(Transaction.user_id == self.user_id,   # type: ignore
                                                db.or_(
                                                    Transaction.transaction_type == TransactionType.LOAN,   # type: ignore
                                                    Transaction.transaction_type == TransactionType.RENEWED
                                                ),
                                                db.or_(
                                                    Transaction.status == TransactionStatus.ACTIVE,
                                                    Transaction.status == TransactionStatus.OVERDUE
                                                )).count()
        
        if active_loans >= self.max_loanable_items:
            return False
        
        if item.item_type == "Computer":

            # Count active computer loans for the user
            active_computers = Transaction.query.filter(Transaction.user_id == self.user_id,    # type: ignore
                                                        db.or_(
                                                        Transaction.transaction_type == TransactionType.LOAN,   # type: ignore
                                                        Transaction.transaction_type == TransactionType.RENEWED
                                                        ),
                                                        Transaction.item_type == "Computer",                 # type: ignore
                                                        db.or_(
                                                            Transaction.status == TransactionStatus.ACTIVE,
                                                            Transaction.status == TransactionStatus.OVERDUE
                                                        )).count()
            
            if active_computers >= self.max_loanable_computers:
                return False
            
        return True
    
    def loan_items(self, item):
        if self.status == MemberStatus.SUSPENDED:
            raise ValueError("Your account is currently suspended. Please contact an Admin for more information.")
        
        if self.has_unpaid_fines():
            raise ValueError("You have unpaid fines. Please pay your fines before being able to checkout more items.")

        if not self.check_loan_limits(item):
            raise ValueError("Loan limit reached. Please return some items before being able to checkout more.")
        return item.loan(self.user_id)
    
    def reserve_items(self, item_id: str):
        from models.Items import Item

        item = Item.query.filter_by(item_id=item_id).first()
        if not item:
            raise ValueError("Item not found.")

        return item.reserve(self.user_id)
    
    def return_items(self, transaction_id: str):

        transaction = Transaction.query.filter_by(transaction_id = transaction_id, user_id = self.user_id).first()
        if not transaction:
            raise ValueError("Transaction not found.")
        
        transaction.completed()
        return True
    
    def renew_loans(self, transaction_id: str):

        transaction = Transaction.query.filter_by(transaction_id = transaction_id, user_id = self.user_id).first()
        if not transaction:
            raise ValueError("Transaction not found.")
        
        transaction.renew()
        return True
    
    def view_transactions(self):
        transactions = Transaction.query.filter_by(user_id = self.user_id).order_by(db.desc(Transaction.date)).all()
        return transactions
    
    def view_fines(self):
        fines = Fine.query.filter_by(user_id = self.user_id).order_by(db.desc(Fine.issued_on)).all()
        return fines
    
    def has_unpaid_fines(self):
        unpaid_fines = Fine.query.filter_by(user_id = self.user_id, status = FineStatus.UNPAID).count()
        return unpaid_fines > 0
    
    def view_reservations(self):
        reservations = Reservation.query.filter_by(user_id = self.user_id).all()
        return reservations
    
    def cancel_reservation(self, reservation_id: str):

        reservation = Reservation.query.filter_by(reservation_id = reservation_id, user_id = self.user_id).first()
        if not reservation:
            raise ValueError("Reservation not found.")
        
        reservation.cancel()
        return True
    
    def get_role(self):
        return UserRole.MEMBER
    
class Admin(User):

    __mapper_args__ = {
        'polymorphic_identity': UserRole.ADMIN
    }

    def __init__(self, name, email, password, phone=None):
        super().__init__(user_id=str(uuid.uuid4()), name = name, email = email, password = password, phone = phone)
        self.role = UserRole.ADMIN
        self.permissions = []

    def promote_to_admin(self, user_id: str):
        user = User.query.filter_by(user_id = user_id).first()
        if not user:
            raise ValueError("User not found. Make sure the user ID is correct.")
        
        user.role = UserRole.ADMIN
        db.session.commit()
        db.session.expire(user)
    
    def demote_to_member(self, user_id: str):
        user = User.query.filter_by(user_id = user_id).first()
        if not user:
            raise ValueError("User not found. Make sure the User ID is correct.")
        
        user.role = UserRole.MEMBER
        if user.member_since is None:
            user.member_since = utcnow()
        if user.status is None:
            user.status = MemberStatus.ACTIVE

        db.session.commit()
        db.session.expire(user)

    def waive_fine(self, fine_id: str):
        fine = Fine.query.filter_by(fine_id = fine_id).first()
        if not fine:
            raise ValueError("Fine not found. Make sure the fine ID is correct.")
        
        fine.waive()
        return True
    
    def approve_reservation(self, reservation_id: str):
        reservation = Reservation.query.filter_by(reservation_id = reservation_id).first()
        if not reservation:
            raise ValueError("Reservation not found. Make sure the reservation ID is correct.")
        
        reservation.mark_ready()
        return True
    
    def manage_user_status(self, user_id, new_status: MemberStatus):
        if not isinstance(new_status, MemberStatus):
            raise ValueError("Invalid status. Status must be either 'Active' or 'Suspended'.")
        
        user = User.query.filter_by(user_id = user_id).first()
        if not user:
            raise ValueError("User not found. Make sure the user ID is correct.")
        
        if user.role != UserRole.MEMBER:
            raise ValueError("Only members can have their status managed.")
        
        user.status = new_status
        db.session.commit()
        return True
        
    def get_role(self):
        return UserRole.ADMIN
    