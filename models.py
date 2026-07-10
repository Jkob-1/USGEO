from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="User")
    @property
    def is_admin(self):
        return self.role == "Admin"

    packages = db.relationship('Package', backref='owner', lazy=True)


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking_number = db.Column(db.String(20), unique=True, nullable=False)
    receiver_name = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="მიღებულია საწყობში")

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref='packages')