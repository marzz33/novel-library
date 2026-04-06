from extensions import db, bcrypt 
from enum import Enum
from datetime import datetime, timezone
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class TransactionType(Enum):
    LOAN = "Loan"
    RENEWED = "Renewed"
    RETURNED = "Returned"

class TransactionStatus(Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"