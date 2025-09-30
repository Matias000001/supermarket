"""Backend module for the SUPERMARKET application."""

import os
import re
import secrets
import time
import sqlite3
import math
import logging

from flask import Flask
from flask import abort
from flask import flash
from flask import make_response
from flask import redirect
from flask import g
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.utils import secure_filename


import config
import items
import users
import messages
import basket


# Initialize the Flask app
app = Flask(__name__)
app.secret_key = config.secret_key


# Logging
logging.basicConfig(level=logging.INFO)


# CSRF validation helper
def check_csrf():
    if request.form.get("csrf_token") != session.get("csrf_token"):
        abort(403)


# Session security settings
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE="Strict",
    PERMANENT_SESSION_LIFETIME=10000
)


def require_login():
    """Ensures the user is logged in, aborts with a 403 if not."""
    if "username" not in session:
        abort(403)


@app.before_request
def before_request():
    """Perform actions before processing each request, such as logging session data."""
    g.start_time = time.time()
    print(f"Session data: {dict(session)}")


@app.after_request
def after_request(response):
    """Logs elapsed time after processing the request."""
    start_time = getattr(g, "start_time", None)
    if start_time is not None:
        elapsed_time = round(time.time() - start_time, 2)
        print("elapsed time:", elapsed_time, "s")
    return response


@app.route("/add_image", methods=["POST"])
def add_image():
    """Handles image upload for the logged-in user."""
    require_login()
    check_csrf()
    user_id = session["id"]
    if "image" not in request.files:
        flash("No file selected", "error")
        return redirect("/user/" + str(user_id))
    file = request.files["image"]
    if file.filename == "":
        flash("No selected file", "error")
        return redirect("/user/" + str(user_id))
    if file and file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        try:
            image = file.read()
            if len(image) > 100 * 1024:
                flash("File too large (max 100KB)", "error")
            else:
                users.update_image(user_id, image)
                flash("Image updated successfully!", "success")
        except (IOError, OSError) as e:
            flash(f"File error: {str(e)}", "error")
        except ValueError as e:
            flash(f"Value error: {str(e)}", "error")
        except RuntimeError as e:
            flash(f"System error: {str(e)}", "error")
    return redirect("/user/" + str(user_id))


@app.route("/user_image/<int:user_id>")
def user_image(user_id):
    """Serves the user"s image."""
    image = users.get_image(user_id)
    if not image:
        abort(404)
    response = make_response(bytes(image))
    response.headers.set("Content-Type", "image/jpeg")
    return response


@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    """Renders the homepage with items and pagination."""
    page_size = 10
    item_count = items.items_count()
    page_count = max(math.ceil(item_count / page_size), 1)
    if page < 1:
        return redirect("/1")
    if page > page_count:
        return redirect(f"/{page_count}")
    current_items = items.get_items(page, page_size)
    return render_template("index.html", page=page, page_count=page_count, items=current_items)


@app.route("/user/<int:user_id>")
def show_user(user_id):
    """Displays a user"s profile with their posted items."""
    user = users.get_user(user_id)
    if not user:
        abort(404)
    user_items = items.get_user_items(user_id)
    if not user_items:
        user_items = []
    image = users.get_image(user_id)
    classes = []
    for i in user_items:
        item_classes = items.get_classes(i["id"])
        if item_classes:
            classes.append(item_classes)
    return render_template("show_user.html", user=user, items=user_items, image=image, classes=classes)


@app.route("/item_image/<int:item_id>")
def item_image(item_id):
    """Serves an item's image."""
    image = items.get_image(item_id)
    if not image:
        abort(404)
    response = make_response(bytes(image))
    response.headers.set("Content-Type", "image/jpeg")
    return response


@app.route("/find_item")
def find_item():
    """Allows the user to search for items based on a query."""
    query = request.args.get("query", "")
    page = int(request.args.get("page", 1))
    results_per_page = 10
    items_found = []
    items_classes = {}
    no_results = False

    if query:
        items_found = items.find_items(query, page, results_per_page)
        total_results = items.get_total_count(query)
        page_count = (total_results + results_per_page - 1) // results_per_page
        if total_results == 0:
            no_results = True
            page_count = 1
        for item in items_found:
            item_id = item["id"]
            item_classes = items.get_classes(item_id)
            items_classes[item_id] = item_classes
    else:
        query = ""
        page_count = 0

    return render_template("find_item.html", query=query, results=items_found,
                           items_classes=items_classes, page=page, page_count=page_count,
                           no_results=no_results)


@app.route("/new_item")
def new_item():
    """Renders the page to add a new item"""
    require_login()
    classes = items.get_all_classes()
    return render_template("new_item.html", classes=classes)


@app.route("/remove_item/<int:item_id>", methods=["GET", "POST"])
def remove_item(item_id):
    """Removes an item from the user"s own inventory."""
    require_login()
    item = items.get_item(item_id)
    if not item:
        abort(404)
    if item["user_id"] != session["id"]:
        abort(403)
    if request.method == "GET":
        return render_template("remove_item.html", item=item)
    if "Remove" in request.form:
        items.remove_item(item_id)
        return redirect("/")
    return redirect(f"/item/{item_id}")


@app.route("/update_item", methods=["POST"])
def update_item():
    require_login()
    check_csrf()
    item_id = request.form["item_id"]
    item = dict(items.get_item(item_id))
    if not item or item["user_id"] != session["id"]:
        abort(403)
    title = request.form["title"]
    description = request.form["description"]
    quantity = request.form["quantity"]
    price = request.form["price"]
    try:
        validate_form_data({
            "title": title,
            "description": description,
            "price": price,
            "quantity": quantity
        })
    except ValueError as e:
        flash(str(e), "error")
        return redirect(f"/edit_item/{item_id}")
    classes = parse_classes_all(request.form.getlist("classes"), items.get_all_classes())
    image_data = None
    remove_image = "remove_image" in request.form
    new_image_file = request.files.get("new_image")
    if new_image_file and new_image_file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        image_data = new_image_file.read()
    elif remove_image:
        image_data = b""
    items.update_item(item_id, title, description, classes, quantity, price, image_data)
    flash("Item updated successfully.", "success")
    return redirect(f"/item/{item_id}")


def is_valid_item(title, description, quantity):
    """Validates the details of a new or updated item."""
    if not title or len(title) > 50:
        return False
    if not description or len(description) > 1000:
        return False
    if not quantity or int(quantity) < 1:
        return False
    return True


def parse_classes_all(class_entries, all_classes):
    """Parses the classes of an item and checks if they are valid."""
    result = []
    for entry in class_entries:
        if entry:
            parts = entry.split(":")
            if len(parts) != 2:
                abort(403)
            if parts[0] not in all_classes or parts[1] not in all_classes[parts[0]]:
                abort(403)
            result.append((parts[0], parts[1]))
    return result


def handle_image_upload_blob(files, form):
    """Handles image upload for an item as a BLOB. Returns image bytes or None."""
    image_file = files.get("new_image")
    if image_file and image_file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        image = image_file.read()
        if len(image) > 100 * 1024:
            raise ValueError("Image too large (max 100KB)")
        return image
    return None


@app.route("/edit_item/<int:item_id>")
def edit_item(item_id):
    """Renders the page to edit an existing item."""
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


@app.route("/item/<int:item_id>", methods=["GET", "POST"])
def show_item(item_id):
    """Displays an item's details along with its associated classes and comments."""
    require_login()
    item = items.get_item(item_id)
    if not item:
        abort(404)
    classes = items.get_classes(item_id)
    comments = items.get_comments(item_id)
    average_rating = items.get_average_rating(item_id)
    if request.method == "POST":
        if "content" in request.form and "rating" in request.form:
            content = request.form["content"]
            rating = int(request.form["rating"])
            user_id = session["id"]
            if user_id:
                try:
                    items.add_comment(item_id, user_id, content, rating)
                    flash("Comment added successfully!", "success")
                except ValueError:
                    flash("Rating must be between 1 and 5.", "danger")
            else:
                flash("You must be logged in to add a comment.", "danger")
            return redirect(url_for("show_item", item_id=item_id))
    return render_template("show_item.html", item=item, classes=classes, comments=comments, average_rating=average_rating)


@app.route("/add_comment", methods=["POST"])
def add_comment_route():
    item_id = request.form["item_id"]
    user_id = session["id"]
    content = request.form["content"]
    rating = request.form["rating"]
    items.add_comment(item_id, user_id, content, rating)
    return redirect(f"/item/{item_id}")


@app.route("/create_item", methods=["POST"])
def create_item():
    """Creates a new item and adds it to the inventory."""
    require_login()
    check_csrf()
    try:
        form_data = extract_form_data(request)
        validate_form_data(form_data)
        user_id = session["id"]
        image_data = None
        image_file = request.files.get("image")
        if image_file:
            if image_file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                image_data = image_file.read()
        classes = parse_classes(request.form.getlist("classes"))
        items.add_item(
            title=form_data["title"],
            description=form_data["description"],
            price=int(form_data["price"]),
            quantity=int(form_data["quantity"]),
            user_id=user_id,
            classes=classes,
            image=image_data
        )
        flash("Product added successfully!", "success")
        return redirect(url_for("index"))
    except ValueError as e:
        app.logger.error("Validation error: %s", e)
        abort(400, str(e))
    except (IOError, OSError) as e:
        app.logger.error("File handling error: %s", e)
        abort(500, "File saving failed")
    except RuntimeError as e:
        app.logger.error("Product addition failed: %s", e)
        abort(500, "Product addition failed")


def extract_form_data(req):
    """Extracts and sanitizes form data for item creation or update."""
    try:
        return {
            "title": req.form["title"].strip(),
            "description": req.form["description"].strip(),
            "price": req.form["price"].strip(),
            "quantity": req.form.get("quantity", "1").strip()
        }
    except KeyError as exc:
        raise ValueError("Required fields are missing") from exc


def validate_form_data(data):
    """Validates form data for item creation or update."""
    if not 0 < len(data["title"]) <= 50:
        raise ValueError("Title must be 1-50 characters long")
    if not 0 < len(data["description"]) <= 1000:
        raise ValueError("Description must be 1-1000 characters.")
    if not re.fullmatch(r"^[1-9][0-9]{0,4}$", data["price"]):
        raise ValueError("Invalid price (1-99999)")
    if not data["quantity"].isdigit() or not 1 <= int(data["quantity"]) <= 9999:
        raise ValueError("Invalid quantity (1-9999)")


def new_image_upload(file):
    """Handles the upload of a new image for an item, ensuring it"s valid and saved."""
    if not file or not file.filename:
        return None
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
        raise ValueError("Allowed formats: .jpg, .jpeg, .png, .webp")
    file.seek(0, os.SEEK_END)
    if file.tell() > 2 * 1024 * 1024:
        raise ValueError("Too big size! (max 2MB)")
    file.seek(0)
    filename_base = f"item_{int(time.time())}"
    file_ext = secure_filename(file.filename).rsplit(".", maxsplit=1)[-1]
    image_filename = f"{filename_base}.{file_ext}"
    file.save(os.path.join(UPLOAD_FOLDER, image_filename))
    return image_filename


def parse_classes(class_list):
    """Parses and validates class entries for an item."""
    classes = []
    all_classes = items.get_all_classes()
    for entry in class_list:
        if not entry:
            continue
        try:
            class_title, class_value = entry.split(":", 1)
        except ValueError as exc:
            raise ValueError("Invalid class format") from exc
        if class_title not in all_classes or class_value not in all_classes[class_title]:
            raise ValueError("Invalid category")
        classes.append((class_title, class_value))
    return classes


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login and redirects after successful login or shows an error."""
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
            session["csrf_token"] = secrets.token_hex(16)
            session.permanent = True
            session.modified = True
            flash("Login successful!", "success")
            return redirect("/")
        flash("Error: Invalid username or password")
        return redirect("/")
    abort(405)


@app.route("/logout")
def logout():
    """Logs the user out and redirects to the homepage."""
    if "username" in session:
        del session["id"]
        del session["username"]
        del session["csrf_token"]
    if "username" in session:
        session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Handles user registration. Renders the registration page (GET) or processes
       the form (POST)."""
    if request.method == "GET":
        return render_template("register.html", filled={})
    if request.method == "POST":
        username = request.form["username"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        # FIXED
        """Validates the registration form inputs and creates a new user if valid."""
        if not username:
            flash("Username cannot be empty", "error")
            return render_template("register.html", filled={})

        if len(username) > 16:
            flash("Username must be 1–16 characters long", "error")
            return render_template("register.html", filled={})

        if not password1 or not password2:
            flash("Password cannot be empty", "error")
            return render_template("register.html", filled={"username": username})

        if len(password1) < 8 or len(password1) > 64:
            flash("Password must be 8-64 characters long", "error")
            return render_template("register.html", filled={"username": username})

        if not re.search(r"[A-Za-z]", password1) or not re.search(r"[0-9]", password1):
            flash("Password must contain both letters and numbers", "error")
            return render_template("register.html", filled={"username": username})
        if password1 != password2:
            flash("Passwords do not match", "error")
            return render_template("register.html", filled={"username": username})
        try:
            users.create_user(username, password1)
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already taken", "error")
            return render_template("register.html", filled={"username": username})
        except sqlite3.OperationalError:
            flash("Database busy, please try again", "error")
            return render_template("register.html", filled={"username": username})
    abort(405)


@app.route("/messages")
def show_messages():
    """Displays the user"s conversations. Redirects to login page if user is not
       logged in."""
    if "id" not in session:
        return redirect("/login")
    user_id = session["id"]
    conversations = messages.get_user_conversations(user_id)
    return render_template("messages.html", conversations=conversations)


@app.route("/send_message/<int:recipient_id>", methods=["POST"])
def send_message(recipient_id):
    """Sends a message to a recipient. Redirects to login if not logged in and
       handles errors."""
    if "id" not in session:
        return redirect("/login")
    content = request.form["content"]
    try:
        messages.send_message(recipient_id, content)
        flash("Message sent successfully", "success")
    except SystemError as e:
        flash(f"Failed to send message: {str(e)}", "danger")
    return redirect("/messages")


@app.route("/delete_conversation/<int:partner_id>", methods=["POST"])
def delete_conversation(partner_id):
    """Deletes a conversation with a partner. Redirects to login if not logged
       in and handles errors."""
    if "id" not in session:
        return redirect("/login")
    try:
        messages.delete_conversation(partner_id)
        flash("Conversation successfully deleted", "success")
    except SystemError as e:
        flash(f"Error while deleting: {str(e)}", "danger")
    return redirect("/messages")


@app.route("/create_purchase", methods=["POST"])
def create_purchase():
    """Creates a purchase for an item, adds it to the cart, and validates quantity
       and item existence."""
    require_login()
    check_csrf()
    item_id = request.form["item_id"]
    if not re.match("^[0-9]+$", item_id):
        abort(403)
    item = items.get_item(item_id)
    if not item:
        abort(403)
    price = request.form["price"]
    quantity = request.form["quantity"]
    seller_id = request.form["seller_id"]
    if not re.match("^[1-9][0-9]*$", quantity):
        abort(403)
    quantity = int(quantity)
    if item["quantity"] < quantity:
        flash("Not enough items in stock", "error")
        return redirect(f"/item/{item_id}")
    user_id = session["id"]
    items.add_purchase(item_id, user_id, seller_id, price, quantity)
    flash(f"Product added to cart ({quantity} kpl)", category="success")
    return redirect("/item/" + str(item_id))



@app.route("/update_basket", methods=["POST"])
def update_basket():
    """Updates item quantities in the cart and ensures they don"t exceed available
       stock."""
    check_csrf()
    if "id" not in session:
        return redirect("/login")
    purchases = basket.get_cart(session["id"])
    product_ids = [purchase["item_id"] for purchase in purchases]
    quantities = basket.get_quantities(product_ids)
    quantities_dict = {item["id"]: item["quantity"] for item in quantities}
    for purchase in purchases:
        quantity = request.form.get(f"quantity_{purchase["purchase_id"]}")
        if quantity:
            quantity = int(quantity)
            max_quantity = quantities_dict.get(purchase["item_id"])
            quantity = min(quantity, max_quantity)
            basket.update_quantity(purchase["purchase_id"], session["id"], quantity)
    return redirect("/basket")


@app.route("/remove_from_basket/<int:purchase_id>", methods=["POST"])
def remove_from_basket(purchase_id):
    """Removes an item from the cart; redirects to login if not logged in."""
    if "id" not in session:
        return redirect("/login")
    check_csrf()
    basket.remove_item(purchase_id, session["id"])
    return redirect("/basket")


@app.route("/checkout", methods=["POST"])
def checkout():
    """Handles checkout by completing the purchase and clearing the cart, or redirects
       if not logged in."""
    if "id" not in session:
        return redirect("/login")
    check_csrf()
    basket.checkout(session["id"])
    return redirect("/")


@app.route("/basket")
def show_basket():
    """Displays the shopping cart or redirects to login if the user is not logged in."""
    if "id" not in session:
        return redirect("/login")
    purchases = basket.get_cart(session["id"])
    product_ids = [purchase["item_id"] for purchase in purchases]
    quantities = basket.get_quantities(product_ids)
    quantities_dict = {item["id"]: item["quantity"] for item in quantities}
    return render_template("basket.html", purchases=purchases, quantities=quantities_dict)
