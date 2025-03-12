from flask import Flask, render_template, request, redirect, url_for
import db

app = Flask(__name__)

@app.teardown_appcontext
def close_connection(exception=None):
    db.close_db()

@app.route("/")
def index():
    messages = db.query("SELECT content FROM messages")
    count = len(messages)
    return render_template("index.html", count=count, messages=messages)

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    content = request.form["content"]
    db.execute("INSERT INTO messages (content) VALUES (?)", [content])
    return redirect("/")