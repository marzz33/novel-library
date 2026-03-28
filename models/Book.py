from models.Items import Item
from app import db

class Book(Item):

    __tablename__= "Books"

    id      = db.Column(db.Integer, db.ForeignKey("Items.id"), primary_key=True)
    isbn    = db.Column(db.String(20), nullable=True)
    author  = db.Column(db.String(200), nullable=False)
    genre   = db.Column(db.String(100), nullable=True)
    edition = db.Column(db.String(50), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'book'
    }

    def __init__(self, title, author, description, qty, isbn=None, genre=None, edition=None):
        super().__init__(title=title, description=description, qty=qty, item_type='book')
        self.author  = author
        self.isbn    = isbn
        self.genre   = genre
        self.edition = edition

    def __repr__(self):
        return f'<Book {self.title}>'