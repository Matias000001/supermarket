"""
This module handles operations related to the user's shopping cart,
including updating quantities, removing items, viewing the cart, and processing the checkout.
"""

import db


def update_quantity(purchase_id, user_id, quantity):
    """Updates the quantity of a cart item for a given user."""
    sql = "UPDATE purchases SET quantity = ? WHERE id = ? AND user_id = ?"
    db.execute(sql, [quantity, purchase_id, user_id])


def remove_item(purchase_id, user_id):
    """Removes a specific item from a user's cart."""
    sql = "DELETE FROM purchases WHERE id = ? AND user_id = ?"
    db.execute(sql, [purchase_id, user_id])


def get_cart(user_id):
    """Fetches a user's cart with details of pending purchases."""
    sql = """SELECT p.id AS purchase_id, i.id AS item_id, i.title, p.quantity, p.price_at_purchase,
                    (p.quantity * p.price_at_purchase) AS total_price
             FROM purchases p
             JOIN items i ON p.item_id = i.id
             WHERE p.user_id = ? AND p.status = 'pending'"""
    return db.query(sql, [user_id])


def checkout(user_id):
    """Marks all pending cart items as paid for a given user."""
    sql = "UPDATE purchases SET status = 'paid' WHERE user_id = ? AND status = 'pending'"
    db.execute(sql, [user_id])


def get_quantities(product_ids):
    """Fetches inventory quantities for given product IDs."""
    if not product_ids:
        return []
    result = ','.join(['?'] * len(product_ids))
    sql = f"SELECT id, quantity FROM items WHERE id IN ({result})"
    return db.query(sql, product_ids)
