from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

class UserRole(Enum):
    GUEST  = "Guest"
    MEMBER = "Member"
    ADMIN  = "Admin"

# Abstract Base Class for Users
class User(ABC):

    def __init__(self, user_id: str, name: str, email: str,
                 password_hash: str, phone: str):
        self._user_id       = user_id
        self._name          = name
        self._email         = email
        self._password      = password_hash
        self._phone         = phone
        self._added_on      = datetime.now()