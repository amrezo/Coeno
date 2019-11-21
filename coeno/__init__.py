from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


app = Flask(__name__)
app.config['SECRET_KEY'] = 'a969af95d4d5dc2d2bba0cb3f0081156'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://amr:vJWfUH88htaK0bTbU6QOwpC0XTIyD6IG@postgres.render.com/coeno_hbht'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from coeno import routes
