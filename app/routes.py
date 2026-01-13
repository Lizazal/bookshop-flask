from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from . import db
from .models import Book, Genre, CartItem, Order, OrderItem, Review

main_bp = Blueprint("main", __name__)


def cart_items():
    return CartItem.query.filter_by(user_id=current_user.id).all()


def cart_total(items):
    return sum(float(i.book.price) * i.quantity for i in items)


def recalculate_book_rating(book_id: int):
    avg_rating, counter = db.session.query(func.avg(Review.rating),
                                           func.count(Review.id)).filter(Review.book_id == book_id).one()
    book = Book.query.get(book_id)
    book.rating = float(avg_rating or 0)
    book.rating_count = int(counter or 0)
    db.session.commit()


@main_bp.route("/")
def index():
    q = (request.args.get("q") or "").strip()
    genres = Genre.query.order_by(Genre.name).all()
    top_books = (Book.query.order_by(Book.rating.desc(),
                                     Book.rating_count.desc()).limit(3).all())
    search_books = []
    if q:
        q_cf = q.casefold()
        all_books = Book.query.order_by(Book.title).all()
        search_books = [book for book in all_books if q_cf in
                        (book.title or "").casefold() or q_cf in
                        (book.author or "").casefold()]
    return render_template("index.html", top_books=top_books, genres=genres, q=q,
                           search_books=search_books)


@main_bp.route("/catalog")
def catalog():
    q = (request.args.get("q") or "").strip()
    genre_id = request.args.get("genre", type=int)
    genres = Genre.query.order_by(Genre.name).all()
    query = Book.query
    if genre_id:
        query = query.join(Book.genres).filter(Genre.id == genre_id)
    books = query.order_by(Book.title).all()
    if q:
        q_cf = q.casefold()
        books = [book for book in books if q_cf in (book.title or "").casefold()
                 or q_cf in (book.author or "").casefold()]
    return render_template("catalog.html", books=books, genres=genres,
                           selected_genre_id=genre_id, q=q)


@main_bp.route("/book/<int:book_id>")
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    reviews = Review.query.filter_by(book_id=book.id).order_by(Review.created_at.desc()).all()
    return render_template("book.html", book=book, reviews=reviews)


@main_bp.route("/book/<int:book_id>/review", methods=["POST"])
@login_required
def review_add_or_update(book_id):
    book = Book.query.get_or_404(book_id)
    rating = request.form.get("rating", type=int)
    text = (request.form.get("text") or "").strip()
    if rating is None or not (1 <= rating <= 5):
        flash("Оценка должна быть от 1 до 5")
        return redirect(url_for("main.book_detail", book_id=book.id))
    review = Review.query.filter_by(user_id=current_user.id, book_id=book.id).first()
    if not review:
        review = Review(user_id=current_user.id, book_id=book.id)
        db.session.add(review)
    review.rating = rating
    review.text = text
    review.created_at = func.now()
    db.session.commit()
    recalculate_book_rating(book.id)
    flash("Отзыв сохранён")
    return redirect(url_for("main.book_detail", book_id=book.id))


@main_bp.route("/cart")
@login_required
def cart():
    items = cart_items()
    return render_template("cart.html", items=items, total=cart_total(items))


@main_bp.route("/cart/add/<int:book_id>", methods=["POST"])
@login_required
def cart_add(book_id):
    book = Book.query.get_or_404(book_id)
    item = CartItem.query.filter_by(user_id=current_user.id, book_id=book.id).first()
    if not item:
        item = CartItem(user_id=current_user.id, book_id=book.id, quantity=0)
        db.session.add(item)
    item.quantity += 1
    db.session.commit()
    flash("Книга добавлена в корзину")
    return redirect(url_for("main.cart"))


@main_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def cart_update(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("Нет доступа")
        return redirect(url_for("main.cart"))
    quantity = request.form.get("quantity", type=int)
    if quantity is None or quantity < 1:
        flash("Количество должно быть >= 1")
        return redirect(url_for("main.cart"))
    item.quantity = quantity
    db.session.commit()
    return redirect(url_for("main.cart"))


@main_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def cart_remove(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash("Нет доступа")
        return redirect(url_for("main.cart"))
    db.session.delete(item)
    db.session.commit()
    flash("Удалено из корзины")
    return redirect(url_for("main.cart"))


@main_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items = cart_items()
    if not items:
        flash("Корзина пуста")
        return redirect(url_for("main.cart"))
    if request.method == "GET":
        return render_template("checkout.html", items=items, total=cart_total(items))
    delivery_method = request.form.get("delivery_method")
    address = (request.form.get("address") or "").strip()
    if delivery_method not in ("pickup", "courier"):
        flash("Выберите способ доставки")
        return redirect(url_for("main.checkout"))
    if delivery_method == "courier" and not address:
        flash("Для доставки до двери нужен адрес")
        return redirect(url_for("main.checkout"))
    order = Order(user_id=current_user.id, status="Создан", delivery_method=delivery_method,
                  address=address if delivery_method == "courier" else None)
    db.session.add(order)
    db.session.flush()
    for item in items:
        db.session.add(OrderItem(order_id=order.id, book_id=item.book_id,
                                 quantity=item.quantity, price=item.book.price))
        db.session.delete(item)
    db.session.commit()
    flash("Заказ оформлен!")
    return redirect(url_for("main.orders"))


@main_bp.route("/orders")
@login_required
def orders():
    orders_list = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=orders_list)
