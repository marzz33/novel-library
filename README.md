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
        rm instance/linrary.db

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
