"""
Module for interacting with the items in the database.
Provides functions to manage items, item classes, purchases,
and retrieve item details, user items, and item statistics.

Functions include adding, updating, and removing items,
handling purchases, and querying items by various parameters.
"""

import db


# Fetches all classes and their values from the database
def get_all_classes():
    """Fetches all classes and values from the database."""
    sql = "SELECT DISTINCT title, value FROM classes ORDER BY id"
    result = db.query(sql)
    classes = {}
    for title, value in result:
        classes.setdefault(title, []).append(value)
    return classes


# Adds a new item to the database
def add_item(title, description, price, quantity, user_id, classes, image_filename=None):
    """Adds a new item to the database."""
    sql = """INSERT INTO items (title, description, price, quantity,
                user_id, image_filename)
             VALUES (?, ?, ?, ?, ?, ?)"""
    db.execute(sql, [title, description, price, quantity, user_id, image_filename])
    item_id = db.last_insert_id()

    sql = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for name, value in classes:
        db.execute(sql, [item_id, name, value])


# Adds a new purchase to the database
def add_purchase(item_id, user_id, seller_id, price, quantity):
    """Adds a new purchase to the database."""
    sql = """INSERT INTO purchases (item_id, user_id, quantity, price_at_purchase, seller_id)
             VALUES (?, ?, ?, ?, ?)"""
    db.execute(sql, [item_id, user_id, quantity, price, seller_id])


# Fetches a user's pending purchases
def get_purchases(user_id):
    """Fetches the user's pending purchases."""
    sql = """SELECT p.id AS purchase_id, i.title AS item_title, p.quantity, p.price_at_purchase,
                    (p.quantity * p.price_at_purchase) AS total_price, i.image_filename
                    FROM purchases p
                    LEFT JOIN items i ON p.item_id = i.id
                    WHERE p.user_id = ? AND p.status = 'pending'"""
    return db.query(sql, [user_id])


# Fetches a user's items
def get_user_items(user_id):
    """Fetches all items belonging to a user."""
    sql = "SELECT id, title, quantity, image_filename FROM items WHERE user_id = ? ORDER BY id DESC"
    return db.query(sql, [user_id])


# Fetches the classes of a given item
def get_classes(item_id):
    """Fetches the classes of a given item."""
    sql = """SELECT title, value
                    FROM item_classes
                    WHERE item_id = ?"""
    return db.query(sql, [item_id])


# Fetches an item's details
def get_item(item_id):
    """Fetches the details of a specific item."""
    sql = """SELECT i.id, i.title, i.description, i.price, i.quantity,
                    u.id AS user_id, u.username, i.image_filename
                    FROM items i
                    JOIN users u ON i.user_id = u.id
                    WHERE i.id = ?"""
    result = db.query(sql, [item_id])
    return result[0] if result else None


# Updates an item's details
def update_item(item_id, title, description, classes, quantity, image_filename=None):
    """Updates the details of an item in the database."""
    sql = "UPDATE items SET title=?, description=?, quantity=?, image_filename=? WHERE id=?"
    db.execute(sql, [title, description, quantity, image_filename, item_id])

    sql = "DELETE FROM item_classes WHERE item_id=?"
    db.execute(sql, [item_id])

    sql = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for name, value in classes:
        db.execute(sql, [item_id, name, value])


# Removes an item from the database
def remove_item(item_id):
    """Removes an item from the database."""
    sql = "DELETE FROM item_classes WHERE item_id = ?"
    db.execute(sql, [item_id])

    sql = "DELETE FROM items WHERE id = ?"
    db.execute(sql, [item_id])


# Searches for items by query
def find_items(query):
    """Searches for items based on a query."""
    sql = """SELECT id, title
                    FROM items
                    WHERE title LIKE ? OR description LIKE ?
                    ORDER BY id DESC"""
    like = "%" + query + "%"
    return db.query(sql, [like, like])


# Fetches the total count of items
def items_count():
    """Fetches the total count of items."""
    sql = "SELECT COUNT(*) FROM items"
    result = db.query(sql)
    return result[0][0] if result else 0


# Fetches items based on pagination
def get_items(page, page_size):
    """Fetches items with pagination."""
    sql = """SELECT i.id, i.title, i.description, i.price, i.quantity,
                    u.id AS user_id, u.username, i.image_filename
             FROM items i
             JOIN users u ON i.user_id = u.id
             ORDER BY i.id DESC
             LIMIT ? OFFSET ?"""
    limit = page_size
    offset = page_size * (page - 1)
    return db.query(sql, [limit, offset])
