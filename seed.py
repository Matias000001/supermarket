import random
import string
import sqlite3
import hashlib

db = sqlite3.connect("database.db")

db.execute("DELETE FROM users")
db.execute("DELETE FROM items")
db.execute("DELETE FROM messages")
db.execute("DELETE FROM purchases")

user_count = 100
item_count = 100
message_count = 100
purchase_count = 100

def random_password_hash():
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return hashlib.sha256(password.encode()).hexdigest()

for i in range(1, user_count + 1):
    db.execute("""INSERT INTO users (username, password_hash) VALUES (?, ?)""",
               [f"user{i}", random_password_hash()])

for i in range(1, item_count + 1):
    user_id = random.randint(1, user_count)
    price = random.randint(10, 500)
    quantity = random.randint(1, 20)
    db.execute("""INSERT INTO items (title, description, price, user_id, quantity, image_filename)
                  VALUES (?, ?, ?, ?, ?, ?)""",
               [f"Item {i}", f"Description {i}", price, user_id, quantity, f"image{i}.jpg"])

for i in range(1, message_count + 1):
    sender_id = random.randint(1, user_count)
    recipient_id = random.randint(1, user_count)
    while recipient_id == sender_id:
        recipient_id = random.randint(1, user_count)
    db.execute("""INSERT INTO messages (content, sender_id, recipient_id)
                  VALUES (?, ?, ?)""",
               [f"Message {i}", sender_id, recipient_id])

for i in range(1, purchase_count + 1):
    item_id = random.randint(1, item_count)
    user_id = random.randint(1, user_count)
    seller_id = random.randint(1, user_count)
    quantity = random.randint(1, 5)
    price = random.randint(10, 500)
    status = random.choice(['pending', 'paid', 'shipped', 'delivered'])
    db.execute("""INSERT INTO purchases (item_id, user_id, quantity, price_at_purchase, seller_id, status)
                  VALUES (?, ?, ?, ?, ?, ?)""",
               [item_id, user_id, quantity, price, seller_id, status])

db.commit()
db.close()
