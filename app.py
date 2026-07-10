from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,logout_user,login_required,current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import random
import string
import os
from groq import Groq
from dotenv import load_dotenv
from forms import LoginForm, RegisterForm, PackageForm, AskForm

app = Flask(__name__)

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

app.config["SECRET_KEY"] = "super-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///delivery.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="User")
    is_banned = db.Column(db.Boolean, default=False)

    @property
    def is_admin(self):
        return self.role == "Admin"


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    tracking_number = db.Column(db.String(20), unique=True, nullable=False)
    receiver_name = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(50), default="მიღებულია საწყობში")

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    owner = db.relationship("User", backref="packages")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_tracking_number():
    return "USG-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=8)
    )


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))

        if not current_user.is_admin:
            flash("Admin access only.")
            return redirect(url_for("home"))

        return f(*args, **kwargs)
    return wrapper


@app.route("/")
@login_required
def home():
    if current_user.is_admin:
        packages = Package.query.all()
    else:
        packages = Package.query.filter_by(user_id=current_user.id).all()

    return render_template("index.html", packages=packages)

@app.route("/ask", methods=["GET", "POST"])
@login_required
def ask_ai():
    form = AskForm()
    answer = None

    if form.validate_on_submit():
        question = form.question.data

        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        answer = chat_completion.choices[0].message.content

    return render_template(
        "ask_ai.html",
        form=form,
        answer=answer
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()

        if existing_user:
            flash("მომხმარებელი უკვე არსებობს.")
            return redirect(url_for("register"))

        user = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data),
            role="User"
        )

        db.session.add(user)
        db.session.commit()

        flash("რეგისტრაცია წარმატებულია.")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and check_password_hash(user.password, form.password.data):

            if user.is_banned:
                flash("თქვენ დაბლოკილი ხართ.")
                return redirect(url_for("login"))

            login_user(user)
            return redirect(url_for("home"))

        flash("არასწორი მონაცემები.")

    return render_template("login.html", form=form)

@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    packages = Package.query.all()
    print("USERS:", users)
    print("PACKAGES:", packages)
    print(User.query.all())
    print(Package.query.all())
    return render_template("admin.html", users=users, packages=packages)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/ship", methods=["GET", "POST"])
@login_required
def ship():
    form = PackageForm()

    if form.validate_on_submit():
        package = Package(
            tracking_number=generate_tracking_number(),
            receiver_name=form.receiver_name.data,
            destination=form.destination.data,
            weight=form.weight.data,
            user_id=current_user.id
        )

        db.session.add(package)
        db.session.commit()

        flash("ამანათი წარმატებით დაემატა.")
        return redirect(url_for("home"))

    return render_template("ship.html", form=form)


@app.route("/track/<tracking_number>")
def track(tracking_number):
    package = Package.query.filter_by(tracking_number=tracking_number).first_or_404()
    return render_template("track.html", package=package)


@app.route("/admin/ban/<int:user_id>")
@login_required
@admin_required
def ban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = True
    db.session.commit()
    flash("User banned.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/unban/<int:user_id>")
@login_required
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_banned = False
    db.session.commit()
    flash("User unbanned.")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/promote/<int:user_id>")
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    user.role = "Admin"
    db.session.commit()
    flash("User promoted to admin.")
    return redirect(url_for("admin_dashboard"))


with app.app_context():
    db.create_all()

with app.app_context():
    user = User.query.filter_by(username="Iakobi").first()
    user.role = "Admin"
    db.session.commit()
    print(user.role)

if __name__ == "__main__":
    app.run(debug=True)
#routes.py-ს ნაცვლად აქ მაქვს ყველაფერი#
#ადმინი არის giorgi pw=1234 და Iakobi pw=1234 დაამატეთ /admin ლინკის ბოლოს მეტი ადმინ პრივილეგიებისთვის <3#