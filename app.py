from flask import Flask
from flask import render_template, request

app = Flask(__name__)

@app.route("/")
def form():
    return render_template("index.html")


