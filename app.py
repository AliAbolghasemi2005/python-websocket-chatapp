from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from cryptography.fernet import Fernet
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET", "supersecret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///chat.db"
db = SQLAlchemy(app)
socketio = SocketIO(app)

key = Fernet.generate_key()
cipher = Fernet(key)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    encrypted = db.Column(db.LargeBinary)