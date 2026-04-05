from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin

app = Flask(__name__)

app.config['SECRET_KEY'] = '2c66c136b4b1add76daaf728a84546294f6c6ee2230594b8'
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

from models import*

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(user_id=user_id).first()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/books')
def books():
    all_books = Book.query.all()
    return render_template('books.html', books=all_books) 

@app.route('/login', methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        # Handle Login logic here .....
        pass
    return render_template('login.html')

@app.route("/signup", methods = ["POST", "GET"])
def signup():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        # Handle signup logic here .....
        pass
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)