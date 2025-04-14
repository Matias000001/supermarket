import math, logging
import os, re, sqlite3, random, time
import config, items, users, messages, basket
from flask import Flask, abort, flash, make_response, redirect
from flask import g, render_template, request, session, url_for
from cryptography.fernet import Fernet
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from datetime import timedelta
from flask_limiter.util import get_remote_address


app = Flask(__name__)
app.secret_key = config.SECRET_KEY

with open("keyfile.key", "rb") as key_file:
    key = key_file.read()
fernet = Fernet(key)

logging.basicConfig(level=logging.INFO)

csrf = CSRFProtect(app)

def validate_csrf():
    if "csrf_token" not in session or "csrf_token" not in request.form:
        return False
    return session["csrf_token"] == request.form["csrf_token"]

limiter = Limiter(
    app=app,
    key_func=lambda: session.get("user_id") or request.headers.get("X-Unique-ID"),
    default_limits=["20000000 per day", "50000000 per hour"]
)

UPLOAD_FOLDER = "static/uploads"
MAX_FILE_SIZE = 1 * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE="Strict",
    PERMANENT_SESSION_LIFETIME=10000
)

if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

def generate_captcha():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    session["captcha_answer"] = str(a + b)
    return f"{a} + {b}"

def require_login():
    if "username" not in session:
        abort(403)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def before_request():
    g.start_time = time.time()
    print(f"Session data: {dict(session)}")

@app.after_request
def after_request(response):
    start_time = getattr(g, 'start_time', None)
    if start_time is not None:
        elapsed_time = round(time.time() - start_time, 2)
        print("elapsed time:", elapsed_time, "s")
    return response

@app.route("/add_image", methods=["GET", "POST"])
def add_image():
    require_login()
    user_id = session["id"]
    if request.method == "GET":
        return render_template("add_image.html")
    if request.method == "POST":
        if 'image' not in request.files:
            flash("No file selected", "error")
            return redirect("/user/" + str(user_id))
        file = request.files["image"]
        if file.filename == '':
            flash("No selected file", "error")
            return redirect("/user/" + str(user_id))
        if file and allowed_file(file.filename):
            try:
                image = file.read()
                if len(image) > 100 * 1024:
                    flash("File too large (max 100KB)", "error")
                    return redirect("/user/" + str(user_id))
                users.update_image(user_id, image)
                flash("Image updated successfully!", "success")
                return redirect("/user/" + str(user_id))
            except Exception as e:
                flash(f"Error: {str(e)}", "error")
                return redirect("/user/" + str(user_id))
    return redirect("/user/" + str(user_id))

@app.route("/user_image/<int:user_id>")
def user_image(user_id):
    image = users.get_image(user_id)
    if not image:
        abort(404)
    response = make_response(bytes(image))
    response.headers.set("Content-Type", "image/jpeg")
    return response

@app.route("/verify_captcha", methods=["POST"])
def verify_captcha():
    if "captcha_answer" not in session:
        flash("CAPTCHA session expired", "error")
        return redirect(url_for("index"))
    user_answer = request.form.get("captcha_answer", "").strip()
    if user_answer == session["captcha_answer"]:
        session["captcha_passed"] = True
        session.pop("captcha_answer", None)
        flash("Verification successful!", "success")
    else:
        flash("Wrong answer, try again", "error")
    return redirect(url_for("index"))

@app.before_request
def require_captcha():
    if request.path in ["/login", "/register"] and not session.get("captcha_passed"):
        abort(403, "Solve CAPTCHA first.")

@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    if "username" in session:
        session.pop("captcha_passed", None)
        session.pop("captcha_passed", None)
        page_size = 10
        item_count = items.items_count()
        page_count = max(math.ceil(item_count / page_size), 1)
        if page < 1:
            return redirect("/1")
        if page > page_count:
            return redirect(f"/{page_count}")
        current_items = items.get_items(page, page_size)
        return render_template("index.html", page=page, page_count=page_count, items=current_items)
    if not session.get("captcha_passed"):
        captcha_question = generate_captcha()
        print("CAPTCHA not passed")
        return render_template("index.html", captcha_question=captcha_question)
    return render_template("index.html")

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    user_items = items.get_user_items(user_id)
    if not user_items:
        user_items = []
    image = users.get_image(user_id)
    return render_template("show_user.html", user=user, items=user_items, image=image)

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
    new_image = request.files.get("new_image")
    image_filename = item["image_filename"]
    if new_image and allowed_file(new_image.filename):
        if image_filename:
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
            except FileNotFoundError:
                pass
        filename = secure_filename(new_image.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        new_image.save(image_path)
        image_filename = filename
    elif "remove_image" in request.form:
        if image_filename:
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
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

@app.route("/create_item", methods=["POST"])
def create_item():
    require_login()
    try:
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        price = request.form["price"].strip()
        quantity = request.form.get("quantity", "1").strip()
    except KeyError:
        abort(400, "Required fields are missing")
    if not (0 < len(title) <= 50):
        abort(400, "Title must be 1-50 characters long")
    if not (0 < len(description) <= 1000):
        abort(400, "Description must be 1-1000 characters.")
    if not re.fullmatch(r"^[1-9][0-9]{0,3}$", price):
        abort(400, "Invalid price (1-9999)")
    if not quantity.isdigit() or not (1 <= int(quantity) <= 999):
        abort(400, "Invalid quantity (1-999)")
    image_filename = None
    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename:
            if not allowed_file(file.filename):
                abort(400, "Allowed formats: .jpg, .jpeg, .png, .webp")
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            if file_size > 2 * 1024 * 1024:
                abort(400, "Too big size! (max 2MB)")
            filename_base = f"item_{int(time.time())}"
            file_ext = secure_filename(file.filename).split(".")[-1]
            image_filename = f"{filename_base}.{file_ext}"
            try:
                file.save(os.path.join(UPLOAD_FOLDER, image_filename))
            except Exception as e:
                app.logger.error(f"Error: With saving : {str(e)}")
                abort(500, "Error: With saving")
    classes = []
    all_classes = items.get_all_classes()
    for entry in request.form.getlist("classes"):
        if entry:
            try:
                class_title, class_value = entry.split(":", 1)
                if class_title not in all_classes or class_value not in all_classes[class_title]:
                    abort(400, "Invalid category")
                classes.append((class_title, class_value))
            except ValueError:
                abort(400, "Invalid class format")
    try:
        items.add_item(
            title=title,
            description=description,
            price=int(price),
            quantity=int(quantity),
            user_id=session["id"],
            classes=classes,
            image_filename=image_filename
        )
        flash("Product added successfully!", "success")
        return redirect(url_for("index"))
    except Exception as e:
        if image_filename:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, image_filename))
            except OSError:
                pass
        app.logger.error(f"Product addition failed: {str(e)}")
        abort(500, "Product addition failed")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        session.clear()
        username = request.form["username"]
        password = request.form["password"]
        user_id = users.check_login(username, password)
        if user_id:
            session["username"] = username
            session["id"] = user_id
            session.permanent = True
            session.modified = True
            flash("Login successful!", "success")
            return redirect("/")
        else:
            flash("Error: Invalid username or password")
            return redirect("/")

@app.route("/logout")
def logout():
    if "username" in session:
        del session["id"]
        del session["username"]
    if "username" in session:
        session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", filled={})
    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if len(username) > 16:
            flash("Too long username! Must be under 16 characters")
            return render_template("register.html", filled={"username": username})
        if password1 != password2:
            flash("Passwords do not match", "error")
            return render_template("register.html", filled={"username": username})
        try:
            users.create_user(username, password1)
            flash("Registration successful! Please login.", "success")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Username already taken", "error")
            return render_template("register.html", filled={"username": username})
        except sqlite3.OperationalError:
            flash("Database busy, please try again", "error")
            return redirect("/")

@app.route("/messages")
def show_messages():
    if "id" not in session:
        return redirect("/login")
    user_id = session["id"]
    conversations = messages.get_user_conversations(user_id)
    return render_template("messages.html", conversations=conversations)

@app.route("/send_message/<int:recipient_id>", methods=["POST"])
def send_message(recipient_id):
    if "id" not in session:
        return redirect("/login")
    content = request.form["content"]
    try:
        messages.send_message(recipient_id, content)
        flash("Message sent successfully", "success")
    except Exception as e:
        flash(f"Failed to send message: {str(e)}", "danger")
    return redirect("/messages")

@app.route("/delete_conversation/<int:partner_id>", methods=["POST"])
def delete_conversation(partner_id):
    if "id" not in session:
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
    if "id" not in session:
        return redirect("/login")
    purchases = basket.get_cart(session["id"])
    product_ids = [purchase["item_id"] for purchase in purchases]
    quantities = basket.get_quantitys(product_ids)
    quantities_dict = {item["id"]: item["quantity"] for item in quantities}
    for purchase in purchases:
        quantity = request.form.get(f"quantity_{purchase["purchase_id"]}")
        if quantity:
            quantity = int(quantity)
            max_quantity = quantities_dict.get(purchase["item_id"])
            if quantity > max_quantity:
                quantity = max_quantity
            basket.update_quantity(purchase["purchase_id"], session["id"], quantity)
    return redirect("/basket")

@app.route("/remove_from_basket/<int:purchase_id>", methods=["POST"])
def remove_from_basket(purchase_id):
    if "id" not in session:
        return redirect("/login")
    basket.remove_item(purchase_id, session["id"])
    return redirect("/basket")

@app.route("/checkout", methods=["POST"])
def checkout():
    if "id" not in session:
        return redirect("/login")
    basket.checkout(session["id"])
    return redirect("/")

@app.route("/basket")
def show_basket():
    if "id" not in session:
        return redirect("/login")
    purchases = basket.get_cart(session["id"])
    product_ids = [purchase["item_id"] for purchase in purchases]
    quantities = basket.get_quantitys(product_ids)
    quantities_dict = {item["id"]: item["quantity"] for item in quantities}
    return render_template("basket.html", purchases=purchases, quantities=quantities_dict)