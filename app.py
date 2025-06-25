from flask import Flask, render_template, request, redirect, session, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import re
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

@app.route("/", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect("/chat")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = username
            return redirect("/chat")
        flash("❌ Invalid username or password.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "username" in session:
        return redirect("/chat")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            flash("❌ Username already exists.")
            return redirect("/register")

        if len(password) < 8 or not re.search(r"[a-zA-Z]", password) or not re.search(r"\d", password):
            flash("❌ Password must be at least 8 characters and include letters and numbers.")
            return redirect("/register")

        hashed = generate_password_hash(password)
        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash("✅ Registration successful! You can now log in.")
        return redirect("/")
    return render_template("register.html")

@app.route("/chat")
def chat():
    if "username" not in session:
        return redirect("/")
    messages = Message.query.all()
    history = []
    for msg in messages:
        try:
            history.append({
                "user": msg.username,
                "message": cipher.decrypt(msg.encrypted).decode()
            })
        except:
            continue
    return render_template("chat.html", username=session["username"], history=history)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@socketio.on("send_message")
def handle_message(data):
    username = session.get("username", "Anonymous")
    encrypted = cipher.encrypt(data["message"].encode())
    msg = Message(username=username, encrypted=encrypted)
    db.session.add(msg)
    db.session.commit()
    decrypted = cipher.decrypt(encrypted).decode()
    emit("receive_message", {"user": username, "message": decrypted}, broadcast=True)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)