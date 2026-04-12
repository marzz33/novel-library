from flask import Flask, render_template, url_for, request, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, LoginManager, UserMixin, current_user

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
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid email or password")
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

@app.route('/transactions')
@login_required
def transactions():
    return render_template('transactions.html', user = current_user)

@app.route('/admin/items')
@login_required
def admin_items():
    if current_user.get_role().value != 'Admin':
        abort(403)
    q = request.args.get('q', '')
    if q:
        items = Item.query.filter(Item.title.ilike(f'%{q}%')).all()
    else:
        items = Item.query.all()
    return render_template('admin-items.html', items=items)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.get_role().value != 'Admin':
        abort(403)
    q = request.args.get('q', '')
    if q:
        users = User.query.filter(
            db.or_(User.name.ilike(f'%{q}%'), User.email.ilike(f'%{q}%'))
        ).all()
    else:
        users = User.query.all()
    return render_template('admin-users.html', users=users)

@app.route('/admin/users/<user_id>/promote', methods=['POST'])
@login_required
def admin_promote_user(user_id):
    if current_user.get_role().value != 'Admin':
        abort(403)
    current_user.promote_to_admin(user_id)
    return redirect(url_for('admin_users'))

@app.route('/admin')
@login_required
def admin():
    if current_user.get_role().value != 'Admin':
        abort(403)
    return render_template('admin-layout.html')

@app.route('/search')
def search():
    q = request.args.get('q', '')
    if q:
        items = Item.query.filter(Item.title.ilike(f'%{q}%')).all()
    else:
        items = []
    return render_template('search-results.html', items=items, q=q)

if __name__ == '__main__':
    app.run(debug=True)