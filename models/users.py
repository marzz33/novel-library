from datetime import datetime, timezone
from enum import Enum
from typing import Any
from app import db, bcrypt
import uuid                                 # Generates new random ID for each user
from flask_login import UserMixin

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class UserRole(Enum):
    GUEST  = "Guest"
    MEMBER = "Member"
    ADMIN  = "Admin"

class MemberStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Suspended"

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
    status          = db.Column(db.Enum(MemberStatus), nullable=False)

    __mapper_args__ = {
            'polymorphic_on':       role,
            'polymorphic_identity': UserRole.GUEST
        }

    def __init__(self, user_id: str, name: str, email: str,
                 password_hash: str, phone: str):
        self.user_id       = str(uuid.uuid4())
        self.name          = name
        self.email         = email
        self.password      = bcrypt.generate_password_hash(password_hash).decode("utf-8")
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
    
    def update_profile(self, name: str = None, email: str = None, phone: str = None):
        if name:
            self.name = name
        if email:
            self.email = email
        if phone:
            self.phone = phone
        db.session.commit()
    