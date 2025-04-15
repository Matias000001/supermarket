"""
This module generates random data to seed the database with users,
items, messages, and purchases for testing purposes.
"""

import random
import string
import sqlite3
import hashlib


# Establish connection to the database
db = sqlite3.connect("database.db")


# Clear existing data
db.execute("DELETE FROM users")
db.execute("DELETE FROM items")
db.execute("DELETE FROM messages")
db.execute("DELETE FROM purchases")


USER_COUNT = 100000
ITEM_COUNT = 1000000
MESSAGE_COUNT = 100000
PURCHASE_COUNT = 100000


def random_password_hash():
    """Generates and returns a random SHA256 password hash."""
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return hashlib.sha256(password.encode()).hexdigest()


# Seed users
for i in range(1, USER_COUNT + 1):
    db.execute("""INSERT INTO users (username, password_hash) VALUES (?, ?)""",
               [f"user{i}", random_password_hash()])


# Seed items
for i in range(1, ITEM_COUNT + 1):
    user_id = random.randint(1, USER_COUNT)
    price = random.randint(10, 500)
    quantity = random.randint(1, 20)
    db.execute("""INSERT INTO items (title, description, price, user_id, quantity, image_filename)
                  VALUES (?, ?, ?, ?, ?, ?)""",
               [f"Item {i}", f"Description {i}", price, user_id, quantity, f"image{i}.jpg"])


# Seed messages
for i in range(1, MESSAGE_COUNT + 1):
    sender_id = random.randint(1, USER_COUNT)
    recipient_id = random.randint(1, USER_COUNT)
    while recipient_id == sender_id:
        recipient_id = random.randint(1, USER_COUNT)
    db.execute("""INSERT INTO messages (content, sender_id, recipient_id)
                  VALUES (?, ?, ?)""",
               [f"Message {i}", sender_id, recipient_id])


# Seed purchases
for i in range(1, PURCHASE_COUNT + 1):
    item_id = random.randint(1, ITEM_COUNT)
    user_id = random.randint(1, USER_COUNT)
    seller_id = random.randint(1, USER_COUNT)
    quantity = random.randint(1, 5)
    price = random.randint(10, 500)
    status = random.choice(['pending', 'paid', 'shipped', 'delivered'])
    db.execute("""INSERT INTO purchases (item_id, user_id, quantity,
                  price_at_purchase, seller_id, status)
                  VALUES (?, ?, ?, ?, ?, ?)""",
               [item_id, user_id, quantity, price, seller_id, status])


# Commit and close the connection
db.commit()
db.close()
