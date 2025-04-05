import sqlite3
from flask import Flask
from flask import abort, redirect, render_template, request, session
from cryptography.fernet import Fernet
import db
import config
import items
import re
import users

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Lue avain tiedostosta
with open("keyfile.key", "rb") as key_file:
    key = key_file.read()

# Käytä avainta Fernet-objektin luomiseen
fernet = Fernet(key)

def require_login():
    if "username" not in session:
        abort(403)

@app.route("/")
def index():
    all_items = items.get_items()
    return render_template("index.html", items = all_items)

# TODO: kesken !!!
@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    
    # Hae käyttäjän myymät tuotteet (jos tarpeen)
    user_items = users.get_items(user_id)
    if not user_items:
        user_items = []

    # Hae käyttäjän ostokset ostoskorista
    purchases = items.get_purchases(user_id)
    print(items.get_purchases(10))

    return render_template("show_user.html", user=user, items=user_items, purchases=purchases)


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
    require_login()
    classes = items.get_all_classes()
    return render_template("new_item.html", classes=classes)

@app.route("/remove_item/<int:item_id>", methods=["POST", "GET"])
def remove_item(item_id):
    require_login()
    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["id"]:
        abort(403)
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
    require_login()
    item_id = request.form["item_id"]
    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["id"]:
        abort(403)
    title = request.form["title"]
    if not title or len(title) > 50:
        abort(403)
    description = request.form["description"]
    if not description or len(description) > 1000:
        abort(403)
    all_classes = items.get_all_classes()
    classes = []
    for entry in request.form.getlist("classes"):
        if entry:
            parts = entry.split(":")
            if parts[0] not in all_classes:
                abort(403)
            if parts[1] not in all_classes[parts[0]]:
                abort(403)
            classes.append((parts[0], parts[1]))
    items.update_item(item_id, title, description, classes)
    return redirect(f"/item/{item_id}")

@app.route("/edit_item/<int:item_id>")
def edit_item(item_id):
    require_login()
    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["id"]:
        abort(403)
    all_classes = items.get_all_classes()
    classes = {}
    for my_class in all_classes:
        classes[my_class] = ""
    for entry in items.get_classes(item_id):
        classes[entry["title"]] = entry["value"]
    return render_template("edit_item.html", item=item, classes=classes, all_classes=all_classes)

@app.route("/item/<int:item_id>")
def show_item(item_id):
    require_login()
    item = items.get_item(item_id)  
    if not item:
        abort(404)
    classes = items.get_classes(item_id)
    return render_template("show_item.html", item=item , classes=classes)

@app.route("/create_item", methods=["POST"])
def create_item():
    require_login()
    title = request.form["title"]
    if not title or len(title) > 50:
        abort(403)
    description = request.form["description"]
    if not description or len(description) > 1000:
        abort(403)
    price = request.form["price"]
    if not re.search("^[1-9][0-9]{0,3}$", price):
        abort(403)
    user_id = session["id"]
    all_classes = items.get_all_classes()
    classes = []
    for entry in request.form.getlist("classes"):
        if entry:
            parts = entry.split(":")
            if parts[0] not in all_classes:
                abort(403)
            if parts[1] not in all_classes[parts[0]]:
                abort(403)
            classes.append((parts[0], parts[1]))
    items.add_item(title, description, price, user_id, classes)
    return redirect("/")

@app.route("/create_purchase", methods=["POST"])
def create_purchase():
    require_login()
    item_id = request.form["item_id"]
    if not re.match("^[0-9]+$", item_id):
        abort(403)
    item = items.get_item(item_id)
    if not item:
        abort(403)
    price = request.form["price"] # TODO: validointi ettei voi laitaa väärää hintaa
    quantity = request.form["quantity"] # TODO validointi ettei voi laittaa väärää määrää
    seller_id = request.form["seller_id"] # TODO validointi ettei voi laittaa väärää myyjä id
    if not re.match("^[1-5]$", quantity):
        abort(403)
    user_id = session["id"]

    items.add_purchase(item_id, user_id, seller_id, price, quantity)
    return redirect("/item/" + str(item_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_id = users.check_login(username, password)
        if user_id:
            session["username"] = username
            session["id"] = user_id
            return redirect("/")
        else:
            return "Error: Invalid username or password"

@app.route("/logout")
def logout():
    if "username" in session:
        del session["id"]
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
        return "Error: Passwords do not match"
    try:
        users.create_user(username, password1)
    except sqlite3.IntegrityError:
        return "Error: Name is already taken"
    return render_template("index.html")


# TODO: siirrä erilliseen tiedostoon
@app.route("/messages")
def messages():
    user_id = session.get('id')
    if not user_id:
        return redirect("/login")

    sql = """WITH conversation_partners AS (
                 SELECT
                     CASE
                         WHEN sender_id = ? THEN recipient_id
                         ELSE sender_id
                     END AS partner_id,
                     MAX(sent_at) AS last_message_time
                 FROM messages
                 WHERE sender_id = ? OR recipient_id = ?
                 GROUP BY partner_id
             )
             SELECT
                 u.id AS partner_id,
                 u.username AS partner_name,
                 m.id AS message_id,
                 m.content,
                 datetime(m.sent_at) AS sent_at,
                 m.sender_id
             FROM conversation_partners cp
             JOIN users u ON cp.partner_id = u.id
             JOIN messages m ON (
                 (m.sender_id = ? AND m.recipient_id = cp.partner_id) OR
                 (m.sender_id = cp.partner_id AND m.recipient_id = ?)
             )
             ORDER BY cp.last_message_time DESC, m.sent_at ASC"""

    messages = db.query(sql, [user_id, user_id, user_id, user_id, user_id])

    conversations = {}
    for msg in messages:
        partner_id = msg['partner_id']
        if partner_id not in conversations:
            conversations[partner_id] = {
                'partner_id': partner_id,
                'partner_name': msg['partner_name'],
                'messages': []
            }

        decrypted_content = fernet.decrypt(msg['content'].encode()).decode()
        conversations[partner_id]['messages'].append({
            'id': msg['message_id'],
            'content': decrypted_content,
            'sent_at': msg['sent_at'],
            'sender_id': msg['sender_id']
        })

    conversation_list = list(conversations.values())
    return render_template("messages.html", conversations=conversation_list)

@app.route("/send_message/<int:recipient_id>", methods=["POST"])
def send_message(recipient_id):
    if 'id' not in session:
        return redirect("/login")
    content = request.form['content']
    sender_id = session['id']
    encrypted_content = fernet.encrypt(content.encode()).decode()
    sql = "INSERT INTO messages (content, sender_id, recipient_id) VALUES (?, ?, ?)"
    db.execute(sql, [encrypted_content, sender_id, recipient_id])
    return redirect("/messages")

@app.route("/delete_conversation/<int:partner_id>", methods=["POST"])
def delete_conversation(partner_id):
    if 'id' not in session:
        return redirect("/login")
    user_id = session['id']
    sql = "DELETE FROM messages WHERE (sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?)"
    db.execute(sql, [user_id, partner_id, partner_id, user_id])
    return redirect("/messages")
