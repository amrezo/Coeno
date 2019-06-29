import secrets
from datetime import datetime
from coeno import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Company(db.Model):
    id = db.Column(db.String(16), primary_key=True, default=secrets.token_hex(16))
    name = db.Column(db.String(120), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default_company.jpg')
    users = db.relationship('User', backref='company', lazy=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(120), unique=True, nullable=False) #owner, admin, or member
    username = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    view_count = db.Column(db.Integer, nullable=True, default=0)
    like_count = db.Column(db.Integer, nullable=True, default=0)
    comment_count = db.Column(db.Integer, nullable=True, default=0)
    type = db.Column(db.String(100), nullable=False) #suggestion, response or notion
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
