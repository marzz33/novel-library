from datetime import datetime, timezone, timedelta
from enum import Enum
from app import db
import uuid

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class MovieFormat(Enum):
    VHS = "VHS"
    DVD = "DVD"
    BLU_RAY = "Blu-ray"
    UHD = "4K UHD"

class Condition(Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"

class Item(db.Model):

    __tablename__ = "Items"

    id                  = db.Column(db.Integer, primary_key = True)
    item_id             = db.Column(db.String(36), unique = True, nullable = False)
    title               = db.Column(db.String(200), nullable = False)
    description         = db.Column(db.String(300), nullable = True)
    qty                 = db.Column(db.Integer, nullable = False)
    available_qty       = db.Column(db.Integer, nullable = False)
    added_on            = db.Column(db.DateTime, default = utcnow)
    item_type           = db.Column(db.String(20), nullable = False)
    loan_days           = 14

    __mapper_args__ = {
        'polymorphic_on': item_type,
        'polymorphic_identity': 'item'
    }

    def __init__(self, title: str, description: str | None, qty: int, item_type: str):
        self.item_id       = str(uuid.uuid4())
        self.title         = title
        self.description   = description
        self.qty           = qty
        self.available_qty = qty
        self.added_on      = utcnow()
        self.item_type     = item_type

    # Returns boolean indicating if the item is currently available for loan (available_qty > 0)
    def check_availability(self) -> bool:
        return self.available_qty > 0
    
    # Returns boolean indicating if the item can be renewed based on its type and any specific rules (e.g. max renewals, holds, etc.)
    # Base method returns False and can be overridden in subclasses for specific item types with their own renewal rules.
    def is_renewable(self) -> bool:
        return False
    
    def get_due_date(self):
       return utcnow() + timedelta(days=self.loan_days)
    
    # Returns item details as a dictionary, used in routes to send data back as JSON
    def get_details(self):
        return {
            "item_id": self.item_id,
            "title": self.title,
            "description": self.description,
            "qty": self.qty,
            "available_qty": self.available_qty,
            "added_on": self.added_on.isoformat(),
            "item_type": self.item_type
        }
    
    # Creates a loan Transaction for this item and decreases available quantity by 1
    def loan(self, user_id: str):

        from models.Transaction import Transaction, TransactionType

        if not self.check_availability():
            raise Exception(f"{self.title} is not available for loan. Please make a reservation.")
        
        self.available_qty -= 1
        transaction = Transaction(
            user_id=user_id,
            item_id=self.item_id,
            transaction_type=TransactionType.LOAN,
            item_type=self.item_type
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction
    
    def reserve(self, user_id: str):

        from models.Reservation import Reservation

        reservation = Reservation(
            user_id = user_id,
            item_id = self.item_id
        )
        db.session.add(reservation)
        db.session.commit()
        return reservation
    
class Book(Item):

    __tablename__ = "Books"

    id = db.Column(db.Integer, db.ForeignKey('Items.id'), primary_key=True)
    isbn = db.Column(db.String(35), unique=True, nullable=True)
    author = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(100), nullable=True)
    genre = db.Column(db.String(150), nullable=True)
    edition = db.Column(db.String(50), nullable=True)
    loan_days = 28

    __mapper_args__ = {
        'polymorphic_identity': 'Book'
    }

    # super() is used to call the __init__ method of the parent Item class to set common attributes,
    # then sets book-specific attributes like isbn, author, etc.
    def __init__(self, title: str, qty: int, author: str, isbn: str | None, publisher: str | None,
                 genre: str | None, edition: str | None, description: str | None):
        super().__init__(title, description, qty, 'Book')
        self.author = author
        self.isbn = isbn
        self.publisher = publisher
        self.genre = genre
        self.edition = edition
    
    # Overrides the base is_renewable method to allow books to be renewable, can add specific rules here if needed (e.g. max renewals, holds, etc.)
    def is_renewable(self):
        return True
    
    def get_details(self):
        details = super().get_details()
        details.update({
            "isbn": self.isbn,
            "author": self.author,
            "publisher": self.publisher,
            "genre": self.genre,
            "edition": self.edition
        })
        return details
    
class Movie(Item):

    __tablename__ = "Movies"

    id = db.Column(db.Integer, db.ForeignKey('Items.id'), primary_key=True)
    genre = db.Column(db.String(100), nullable=True)
    rating = db.Column(db.String(10), nullable=True)
    format = db.Column(db.Enum(MovieFormat), nullable=False)
    release_year = db.Column(db.Integer, nullable=True)
    director = db.Column(db.String(100), nullable=False)
    loan_days = 7

    __mapper_args__ = {
        'polymorphic_identity': 'Movie'
    }

    def __init__(self, title: str, qty: int, format: MovieFormat, genre: str | None, rating: str | None,
                release_year: int | None, director: str | None, description: str | None):
        super().__init__(title, description, qty, 'Movie')
        self.format = format
        self.genre = genre
        self.rating = rating
        self.release_year = release_year
        self.director = director
    
    def is_renewable(self):
        return True

    def get_details(self):
        details = super().get_details()
        details.update({
            "genre": self.genre,
            "rating": self.rating,
            "format": self.format.value,
            "release_year": self.release_year,
            "director": self.director
        })
        return details

class Computer(Item):

    __tablename__ = "Computers"
    
    id = db.Column(db.Integer, db.ForeignKey('Items.id'), primary_key=True)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    os = db.Column(db.String(50), nullable=False)
    specs = db.Column(db.String(350), nullable=True)
    brand = db.Column(db.String(50), nullable=True)
    condition = db.Column(db.Enum(Condition), nullable=False)
    last_maintenance = db.Column(db.DateTime, nullable=True)
    loan_days = 140

    __mapper_args__ = {
        'polymorphic_identity': 'Computer'
    }
    
    def __init__(self, title: str, qty: int, serial_number: str,
                 os: str, condition: Condition, brand: str | None = None,
                 specs: str | None = None, description: str | None = None,
                 last_maintenance: datetime | None = None):
        super().__init__(title, description, qty, 'Computer')
        self.serial_number = serial_number
        self.os = os
        self.condition = condition
        self.brand = brand
        self.specs = specs
        self.last_maintenance = last_maintenance

    def is_renewable(self):
        return False
    
    def get_details(self):
        details = super().get_details()
        details.update({
            "serial_number": self.serial_number,
            "os": self.os,
            "specs": self.specs,
            "brand": self.brand,
            "condition": self.condition.value,
            "last_maintenance": self.last_maintenance.isoformat() if self.last_maintenance else None
        })
        return details