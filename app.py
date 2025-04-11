import os, re, sqlite3
import config, items, users, messages, basket
import logging
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from cryptography.fernet import Fernet
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


app = Flask(__name__)
app.secret_key = config.SECRET_KEY

with open("keyfile.key", "rb") as key_file:
    key = key_file.read()
fernet = Fernet(key)

logging.basicConfig(level=logging.INFO)

csrf = CSRFProtect(app)

limiter = Limiter(
    app=app,
    key_func=lambda: session.get('user_id') or request.headers.get('X-Unique-ID'),  # Riippuu käyttäjästä, ei IP:stä
    default_limits=["30 per minute", "500 per day"]
)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,     # Eväste ei ole luettavissa JS:llä
    SESSION_COOKIE_SECURE=True,       # HTTPS
    SESSION_COOKIE_SAMESITE='Strict', # CSRF suoja
    PERMANENT_SESSION_LIFETIME=3600   # Sessionin voimassaoloaika sekunteina
)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def require_login():
    if "username" not in session:
        abort(403)

@app.route("/")
def index():
    all_items = items.get_items()
    return render_template("index.html", items = all_items)

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    user_items = items.get_user_items(user_id)
    if not user_items:
        user_items = []
    return render_template("show_user.html", user=user, items=user_items)

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
    item = dict(items.get_item(item_id))
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
    quantity = request.form["quantity"]
    if not quantity or int(quantity) < 1:
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
    new_image = request.files.get('new_image')
    image_filename = item["image_filename"]
    if new_image and allowed_file(new_image.filename):
        if image_filename:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            except FileNotFoundError:
                pass
        filename = secure_filename(new_image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        new_image.save(image_path)
        image_filename = filename
    elif 'remove_image' in request.form:
        if image_filename:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            except FileNotFoundError:
                pass
        image_filename = None
    items.update_item(item_id, title, description, classes, quantity, image_filename)
    flash("Item updated successfully.", "success")
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
    return render_template("show_item.html", item=item, classes=classes)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/create_item", methods=["POST"])
def create_item():
    require_login()
    title = request.form["title"]
    description = request.form["description"]
    price = request.form["price"]
    quantity = request.form.get("quantity", "1")
    if not title or len(title) > 50:
        abort(403)
    if not description or len(description) > 1000:
        abort(403)
    if not re.search("^[1-9][0-9]{0,3}$", price):
        abort(403)
    if not quantity.isdigit() or int(quantity) < 1:
        abort(403)
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            image_filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, image_filename))
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
    items.add_item(title, description, price, quantity, user_id, classes, image_filename)
    return redirect("/")

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
    if "username" in session:
        session.clear()
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

@app.route("/messages")
def show_messages():
    if 'id' not in session:
        return redirect("/login")
    user_id = session['id']
    conversations = messages.get_user_conversations(user_id)
    return render_template("messages.html", conversations=conversations)

@app.route("/send_message/<int:recipient_id>", methods=["POST"])
def send_message(recipient_id):
    if 'id' not in session:
        return redirect("/login")
    content = request.form['content']
    try:
        messages.send_message(recipient_id, content)
        flash("Message sent successfully", "success")
    except Exception as e:
        flash(f"Failed to send message: {str(e)}", "danger")
    return redirect("/messages")

@app.route("/delete_conversation/<int:partner_id>", methods=["POST"])
def delete_conversation(partner_id):
    if 'id' not in session:
        return redirect("/login")
    try:
        messages.delete_conversation(partner_id)
        flash("Conversation successfully deleted", "success")
    except Exception as e:
        flash(f"Error while deleting: {str(e)}", "danger")
    return redirect("/messages")

@app.route("/create_purchase", methods=["POST"])
def create_purchase():
    require_login()
    item_id = request.form["item_id"]
    if not re.match("^[0-9]+$", item_id):
        abort(403)
    item = items.get_item(item_id)
    if not item:
        abort(403)
    price = request.form["price"]
    quantity = request.form["quantity"]
    seller_id = request.form["seller_id"]
    if not re.match("^[1-5]$", quantity):
        abort(403)
    user_id = session["id"]
    items.add_purchase(item_id, user_id, seller_id, price, quantity)
    flash(f"Product added to cart({quantity} kpl)", category="success")
    return redirect("/item/" + str(item_id))

@app.route("/update_basket", methods=["POST"])
def update_basket():
    if 'id' not in session:
        return redirect('/login')
    purchases = basket.get_cart(session['id'])
    product_ids = [purchase['item_id'] for purchase in purchases]
    quantities = basket.get_quantitys(product_ids)
    quantities_dict = {item['id']: item['quantity'] for item in quantities}
    for purchase in purchases:
        quantity = request.form.get(f"quantity_{purchase['purchase_id']}")
        if quantity:
            quantity = int(quantity)
            max_quantity = quantities_dict.get(purchase['item_id'])
            if quantity > max_quantity:
                quantity = max_quantity
            basket.update_quantity(purchase['purchase_id'], session['id'], quantity)
    return redirect("/basket")

@app.route("/remove_from_basket/<int:purchase_id>", methods=["POST"])
def remove_from_basket(purchase_id):
    if 'id' not in session:
        return redirect('/login')
    basket.remove_item(purchase_id, session['id'])
    return redirect("/basket")

@app.route("/checkout", methods=["POST"])
def checkout():
    if 'id' not in session:
        return redirect('/login')
    basket.checkout(session['id'])
    return redirect("/")

@app.route("/basket")
def show_basket():
    if 'id' not in session:
        return redirect('/login')
    purchases = basket.get_cart(session['id'])
    product_ids = [purchase['item_id'] for purchase in purchases]
    quantities = basket.get_quantitys(product_ids)
    quantities_dict = {item['id']: item['quantity'] for item in quantities}
    return render_template("basket.html", purchases=purchases, quantities=quantities_dict)