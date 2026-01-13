import random
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from . import db, login_manager
from .models import User


auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")

    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    phone = (request.form.get("phone") or "").strip()
    password = (request.form.get("password") or "").strip()
    if not (name and email and phone and password):
        flash("Заполните все поля")
        return redirect(url_for("auth.register"))
    if User.query.filter_by(email=email).first():
        flash("Пользователь с таким email уже существует")
        return redirect(url_for("auth.register"))

    code = str(random.randint(100000, 999999))
    session["pending_user"] = {"name": name, "email": email, "phone": phone, "password": password}
    session["verify_code"] = code
    flash(f"Код подтверждения: {code}")
    return redirect(url_for("auth.verify"))


@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "GET":
        if "pending_user" not in session:
            flash("Нет данных для подтверждения. Зарегистрируйтесь заново.")
            return redirect(url_for("auth.register"))
        return render_template("auth/verify.html")

    entered = (request.form.get("code") or "").strip()
    real = session.get("verify_code")
    data = session.get("pending_user")
    if not real or not data:
        flash("Сессия подтверждения истекла. Зарегистрируйтесь заново.")
        return redirect(url_for("auth.register"))
    if entered != real:
        flash("Неверный код")
        return redirect(url_for("auth.verify"))

    user = User(name=data["name"], email=data["email"], phone=data["phone"], password=data["password"])
    db.session.add(user)
    db.session.commit()

    session.pop("pending_user", None)
    session.pop("verify_code", None)
    login_user(user)
    flash("Регистрация завершена")
    return redirect(url_for("main.index"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()
    user = User.query.filter_by(email=email).first()
    if not user or user.password != password:
        flash("Неверный email или пароль")
        return redirect(url_for("auth.login"))

    login_user(user)
    flash("Вы вошли в аккаунт")
    return redirect(url_for("main.index"))


@auth_bp.route("/logout", methods=["GET"])
@login_required
def logout_confirm():
    return render_template("auth/logout_confirm.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта")
    return redirect(url_for("main.index"))
