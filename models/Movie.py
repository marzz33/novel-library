from models.Items import Item
from app import db

class Movie(Item):

    __tablename__= "Movies"

    id             = db.Column(db.Integer, db.ForeignKey("Items.id"), primary_key=True)
    genre          = db.Column(db.String(100), nullable=True)
    rating         = db.Column(db.String(20), nullable=True)
    format         = db.Column(db.String(200), nullable=False)
    release_year   = db.Column(db.Integer, nullable=True)
    director       = db.Column(db.String(200), nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'movie'
    }

    def __repr__(self):
        return f'<Movie {self.title}>'