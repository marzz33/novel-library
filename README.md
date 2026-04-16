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

 6. if running for the first time, populate the inventory by running:
        python seed.py
    
 7. after package is initialized and seed is loaded, run the app:
          python app.py
          
 8. open app in browser by searching for:
          http://localhost:5000/
