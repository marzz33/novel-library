from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from app import db, bcrypt
import uuid                                 # Generates new random ID for each user
from flask_login import UserMixin

class UserRole(Enum):
    GUEST  = "Guest"
    MEMBER = "Member"
    ADMIN  = "Admin"

class MemberStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Suspended"

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

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

    __mappper_args__ = {
            'polymorphic_on':       role,
            'polymorphic_identity': 'user'
        }

    def __init__(self, user_id: str, name: str, email: str,
                 password_hash: str, phone: str):
        self._user_id       = str(uuid.uuid4())
        self._name          = name
        self._email         = email
        self._password      = bcrypt.generate_password_hash(password_hash).decode("utf-8")
        self._phone         = phone
        self._added_on      = utcnow()