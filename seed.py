import csv
from app import app, db
from models.Items import Book, Movie, Computer, MovieFormat, Condition
from models.users import Admin


with app.app_context():
    db.create_all()

    # --- Books ---
    with open("data/books.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip if this ISBN is already in the database
            if Book.query.filter_by(isbn=row["isbn"]).first():
                continue

            book = Book(
                title=row["title"],
                author=row["author"],
                isbn=row["isbn"],
                publisher=row["publisher"] or None,
                genre=row["genre"] or None,
                edition=row["edition"] or None,
                qty=int(row["qty"]),
                description=row["description"] or None
            )
            db.session.add(book)
    print("Books loaded.")

    # --- Movies ---
    with open("data/movies.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if Movie.query.filter_by(title=row["title"], director=row["director"]).first():
                continue

            movie = Movie(
                title=row["title"],
                director=row["director"],
                format=MovieFormat(row["format"]),
                genre=row["genre"] or None,
                rating=row["rating"] or None,
                release_year=int(row["release_year"]) if row["release_year"] else None,
                qty=int(row["qty"]),
                description=row["description"] or None
            )
            db.session.add(movie)
    print("Movies loaded.")

    # --- Computers ---
    with open("data/computers.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if Computer.query.filter_by(serial_number=row["serial_number"]).first():
                continue

            computer = Computer(
                title=row["title"],
                serial_number=row["serial_number"],
                os=row["os"],
                condition=Condition(row["condition"]),
                brand=row["brand"] or None,
                specs=row["specs"] or None
            )
            db.session.add(computer)
    print("Computers loaded.")

    db.session.commit()
    print("Done.")