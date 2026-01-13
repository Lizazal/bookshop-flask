# Для однократного импорта данных из файла, отдельно от работы приложения
# app/data_import.py
import json
from app import create_app, db
from app.models import Book, Genre

app = create_app()

with app.app_context():
    db.create_all()
    with open("../data/books_catalog.json", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        genre = Genre.query.filter_by(name=item["genre"]).first()
        if not genre:
            genre = Genre(name=item["genre"])
            db.session.add(genre)
        book = Book(
            title=item["title"],
            author=item["author"],
            price=item["price"],
            year=item.get("year"),
            cover=item.get("cover"),
            description=item.get("description"),
            rating=item.get("rating", 0),
        )
        book.genres.append(genre)
        db.session.add(book)
    db.session.commit()
print("Импорт завершён")
