from models.Items import Item
from app import db

class Computer(Item):

    __tablename__= "Computers"

    id               = db.Column(db.Integer, db.ForeignKey("Items.id"), primary_key=True)
    serial_number    = db.Column(db.String(50), nullable=True)
    operating_system = db.Column(db.String(50), nullable=True)
    specs            = db.Column(db.String(50), nullable=True)
    brand            = db.Column(db.String(50), nullable=True)
    condition        = db.Column(db.String(50), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'computer'
    }

    def __repr__(self):
        return f'<Computer {self.title}>'