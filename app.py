import sqlite3
from flask import Flask
from flask import abort, redirect, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config
import items

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    all_items = items.get_items()
    return render_template("index.html", items = all_items)

@app.route("/find_item")
def find_item():
    query = request.args.get("query")
    if query:
        items_found = items.find_items(query)
    else:
        query = ""
        items_found = []
    return render_template("find_item.html", query=query, results=items_found)

@app.route("/new_item")
def new_item():
    return render_template("new_item.html")

@app.route("/remove_item/<int:item_id>", methods=["POST", "GET"])
def remove_item(item_id):
    item = items.get_item(item_id)
    if item["user_id"] != session["id"]:
        abort(403)  # Forbidden

    if request.method == "GET":
        return render_template("remove_item.html", item=item)
    if request.method == "POST":
        if "Remove" in request.form:
            items.remove_item(item_id)
            return redirect("/")
        else:
            return redirect(f"/item/{item_id}")

@app.route("/update_item", methods=["POST"])
def update_item():
    item_id = request.form["item_id"]
    item = items.get_item(item_id)
    if item["user_id"] != session["id"]:
        abort(403)  # Forbidden

    title = request.form["title"]
    description = request.form["description"]

    items.update_item(item_id, title, description)  

    return redirect(f"/item/{item_id}")



@app.route("/edit_item/<int:item_id>")
def edit_item(item_id):
    item = items.get_item(item_id)

    if item["user_id"] != session["id"]:
        abort(403)  # Forbidden

    return render_template("edit_item.html", item=item)


@app.route("/item/<int:item_id>")
def show_item(item_id):
    item = items.get_item(item_id)  
    return render_template("show_item.html", item = item)

@app.route("/create_item", methods=["POST"])
def create_item():
    title = request.form["title"]
    description = request.form["description"]
    price = request.form["price"]
    user_id = session["id"]
    items.add_item(title, description, price, user_id)  
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # SQL-kysely, joka hakee salasanan hashi käyttäjätunnuksella
        sql = "SELECT id, password_hash FROM users WHERE username = ?"
        result = db.query(sql, [username])
        if result:
            result = result[0]
            user_id = result["id"]
            password_hash = result["password_hash"]
            if check_password_hash(password_hash, password):
                session["username"] = username
                session["id"] = user_id
                print(f"User ID stored in session: {session.get('id')}")  # Lisätty tarkistus
                return redirect("/")
            else:
                return "VIRHE: väärä salasana"
        else:
            return "VIRHE: käyttäjätunnus ei löytynyt"

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"
    password_hash = generate_password_hash(password1)
    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"
    return redirect("/")
