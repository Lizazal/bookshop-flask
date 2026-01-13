from datetime import datetime
from flask_login import UserMixin
from . import db

book_genres = db.Table(
    "book_genres",
    db.Column("book_id", db.Integer, db.ForeignKey("book.id")),
    db.Column("genre_id", db.Integer, db.ForeignKey("genre.id")),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    phone = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    def __repr__(self):
        return f"<Genre {self.name}>"


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(120), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    genres = db.relationship("Genre", secondary=book_genres, backref="books")
    cover = db.Column(db.String(255))
    description = db.Column(db.Text)
    year = db.Column(db.Integer)
    rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Book {self.title}>"


class CartItem(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "book_id", name="unique_cart_user_book"),
                      db.CheckConstraint("quantity >= 1", name="check_cart_quantity_positive"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    book = db.relationship("Book")

    def __repr__(self):
        return f"<CartItem user={self.user_id} book={self.book_id}>"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(50), default="Создан")
    address = db.Column(db.String(255))
    delivery_method = db.Column(db.String(20), nullable=False, default="pickup")
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.id}>"


class OrderItem(db.Model):
    __table_args__ = (db.CheckConstraint("quantity >= 1", name="check_orderitem_quantity_positive"),)
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    book = db.relationship("Book")

    def __repr__(self):
        return f"<OrderItem {self.book_id} quantity {self.quantity}>"


class Review(db.Model):
    __table_args__ = (db.UniqueConstraint("user_id", "book_id", name="unique_review_user_book"),
                      db.CheckConstraint("rating >= 1 AND rating <= 5", name="check_review_rating_range"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Review book={self.book_id} rating={self.rating}>"
