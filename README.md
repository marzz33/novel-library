# novel-library

You need pip

 To edit...

 1. clone repository
 
 2. Create virtual environment to run app.py:
          python -m venv env
    
 4. activate the virtual environment(windows):
          env\Scripts\activate

    If using Linux, run this on the termial:
        source env/bin/activate
    
 5. download requirements from txt file:
          pip install -r requirements.txt

 6. To restart your database (new changes to the CSV fils) delete the database with:
        rm instance/library.db

 7. after package is initialized, run the app (if database is empty it will automatically upload the inventory during boot up):
          python app.py
          
 8. open app in browser by searching for:
    http://localhost:5000/

Instructions for setting up admin account

1. git pull first: 

    git pull origin main

2. activate env: 
    
    env\Scripts\Activate.ps1

3. Recreate database: 

    flask shell
    from app import db
    db.create_all()
    exit()

4. Create an admin account

    flask shell

    from models.users import Admin
    from app import db
    admin = Admin(name="Admin", email="admin@test.com", password="password123")
    db.session.add(admin)
    db.session.commit()
    print("Created admin")
    exit()

5. Run appp

    flask run

6. GO TO : http://127.0.0.1:5000/login and login with

    email: admin@test.com
    password: password123

Instructions to create/test fines through shell

1. open shell/terminal

    flask shell
    from app import db
    from models import User, Transaction, Fine

2. retrieves a specific user and first transaction

    user = User.query.filter_by(email = "email@example.com").first()
    t = Transaction.query.first()

    note: insert your user email in the 'email@example.com'

3. create fine

    fine = Fine(user_id=user.user_id, transaction_id=t.transaction_id, reason="did not return item on time", amount=10.00)
    db.session.add(fine)
    db.session.commit()
    exit()

    note: you can write any reason and amount

To delete fine from specific user:

1. open shell

    flask shell
    from app import db
    from models import User, Fine

2. select specific user and fine from table

    user = User.query.filter_by(email = "email@example.com").first()
    fine = Fine.query.filter_by(user_id=user.user_id).first()

    note: insert your user email in the 'email@example.com'

3. delete that fine

    db.session.delete(fine)
    db.session.commit()
    exit()

