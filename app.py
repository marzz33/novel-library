from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)

app.config['SECRET_KEY'] = '2c66c136b4b1add76daaf728a84546294f6c6ee2230594b8'
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(200), nullable=True)
    genre = db.Column(db.String(200), nullable=True)
    edition = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Book {self.title}>'

@app.route('/')
def index():
    return "Running novel yay"

if __name__ == '__main__':
    app.run(debug=True)