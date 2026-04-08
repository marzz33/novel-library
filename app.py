from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin, current_user
from sqlalchemy import inspect
import os
from extensions import db, bcrypt 
from models.users import Member, User 
from models.users import Member,User, Admin

app = Flask(__name__)

app.config['SECRET_KEY'] = '2c66c136b4b1add76daaf728a84546294f6c6ee2230594b8'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'

bcrypt.init_app(app)
db.init_app(app)

import models.users
import models.Items
import models.Transaction 
import models.Fine 
import models.Reservation
import models.Notification


login_manager = LoginManager()
login_manager.init_app(app)



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
        # Handle Login logic here ..... DONE BY ME(Caleb)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for ('profile'))
        
        
        return "Invalid email or password"

    return render_template('login.html')

@app.route("/signup", methods = ["POST", "GET"])
def signup():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        # Handle signup logic here .....
         #NEW CODE ADDED BY ME (CALEB D)
        
        hashed_pw = bcrypt.generate_password_hash(password)
        
        existing_user = User.query.filter_by(email=email).first()
        
        if existing_user:
            return "Email already exists. Try logging in"

    
        new_user = Member(name=name , email = email , password_hash = password)
        
        db.session.add(new_user)
        db.session.commit()

        return redirect (url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods = ["POST", "GET"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        current_user.update_profile(name=name, email=email, phone=phone)
        return redirect(url_for('profile'))
    return render_template('profile.html', user = current_user)

        #Created by Me (Caleb Dotson)

@app.route('/create-admin')
def create_admin():
    admin = Admin(
        name = "Admin",
        email= "admin@test.com",
        password_hash ="1234"

    )
    
    db.session.add(admin)
    db.session.commit()

    return "Admin created"

@app.route('/admin')
@login_required
def admin_page():
    if not current_user.is_admin():
        return "Access denied" , 403
        
    return "Welcome, Admin"
    
@app.route('/promote/<user_id>')
@login_required
def promote(user_id):
        if not current_user.is_admin():

            return "Access denied" , 403 

        current_user.promote_to_admin(user_id)
        return "User promoted"





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("DB file should be in statnce /library.db")
        print("Exists:", os.path.exists ("instance/library.db"))
        print("Tables: ", inspect(db.engine).get_table_names())
    app.run(debug=True)