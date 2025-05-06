"""
This module generates random data to seed the database with users,
items, messages, and purchases for testing purposes.
"""

import random
import sqlite3



db = sqlite3.connect("database.db")


db.execute("DELETE FROM comments")
db.execute("DELETE FROM purchases")
db.execute("DELETE FROM messages")
db.execute("DELETE FROM item_classes")
db.execute("DELETE FROM items")
db.execute("DELETE FROM users")
db.execute("DELETE FROM classes")



user_count = 10**6
item_count = 10**6
class_count = 1000
message_count = 10**6
purchase_count = 10**6
comment_count = 10**6


for i in range(1, user_count + 1):
    username = f"user{i}"
    password = f"password{i}"
    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
               [username, password])
    

for i in range(1, class_count + 1):
    db.execute("INSERT INTO classes (id, title, value) VALUES (?, ?, ?)",
               [i, f"class_title{i}", f"class_value{i}"])


for i in range(1, item_count + 1):
    title = f"item_title{i}"
    description = f"Item description {i}"
    price = random.randint(10, 1000)
    user_id = random.randint(1, user_count)
    quantity = random.randint(1, 100)
    db.execute("INSERT INTO items (title, description, price, user_id, quantity) VALUES (?, ?, ?, ?, ?)",
               [title, description, price, user_id, quantity])


    for j in range(random.randint(1, 3)):
        class_id = random.randint(1, class_count)
        db.execute("INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)",
                   [i, f"class_title{class_id}", f"class_value{class_id}"])


for i in range(1, message_count + 1):
    sender_id = random.randint(1, user_count)
    recipient_id = random.randint(1, user_count)
    while sender_id == recipient_id:
        recipient_id = random.randint(1, user_count)

    db.execute("INSERT INTO messages (content, sender_id, recipient_id) VALUES (?, ?, ?)",
               [f"message_content{i}", sender_id, recipient_id])


for i in range(1, purchase_count + 1):
    item_id = random.randint(1, item_count)
    user_id = random.randint(1, user_count)
    quantity = random.randint(1, 5)
    price_at_purchase = random.randint(10, 1000)
    seller_id = random.randint(1, user_count)
    status = random.choice(["pending", "paid", "shipped", "delivered"])

    db.execute("INSERT INTO purchases (item_id, user_id, quantity, price_at_purchase, status, seller_id) VALUES (?, ?, ?, ?, ?, ?)",
               [item_id, user_id, quantity, price_at_purchase, status, seller_id])


for i in range(1, comment_count + 1):
    item_id = random.randint(1, item_count)
    user_id = random.randint(1, user_count)
    rating = random.randint(1, 5)
    db.execute("INSERT INTO comments (item_id, user_id, content, rating) VALUES (?, ?, ?, ?)",
               [item_id, user_id, f"comment_content{i}", rating])


db.commit()
db.close()