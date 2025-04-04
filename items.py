import db

def get_all_classes():
    sql = "SELECT title, value FROM classes ORDER BY id"
    result = db.query(sql)
    classes = {}
    for title, value in result:
        classes[title] = []
    for title, value in result:
        classes[title].append(value)
    return classes

def add_item(title, description, price, user_id, classes):
    sql = """INSERT INTO items (title, description, price, user_id) 
          VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, description, price, user_id])
    item_id = db.last_insert_id()

    sql = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for title, value in classes:
        db.execute(sql, [item_id, title, value])

def add_purchase(item_id, user_id, seller_id, price, quantity):
    sql = """INSERT INTO purchases (item_id, user_id, quantity, price_at_purchase, seller_id) 
             VALUES (?, ?, ?, ?, ?)"""
    db.execute(sql, [item_id, user_id, quantity, price, seller_id])

def get_purchases(user_id):
    sql = """SELECT p.id AS purchase_id,
                    i.title AS item_title,
                    p.quantity,
                    p.price_at_purchase,
                    (p.quantity * p.price_at_purchase) AS total_price
             FROM purchases p
             LEFT JOIN items i ON p.item_id = i.id
             WHERE p.user_id = ? AND p.status = 'pending'"""
    return db.query(sql, [user_id])

def get_items():
    sql = "SELECT id, title FROM items ORDER BY id DESC"
    return db.query(sql)

def get_classes(item_id):
    sql = """SELECT title, value 
             FROM item_classes
             WHERE item_id = ?"""
    return db.query(sql, [item_id])

def get_item(item_id):
    sql = """SELECT items.id,
                    items.title, 
                    items.description, 
                    items.price, 
                    users.id user_id,
                    users.username 
            FROM items,users 
            WHERE items.user_id = users.id AND
                    items.id = ?"""
    result = db.query(sql, [item_id])
    return result[0] if result else None

def update_item(item_id, title, description, classes):
    sql = """UPDATE items SET title = ?, description = ? 
            WHERE id = ?"""
    db.execute(sql, [title, description, item_id])

    sql = "DELETE FROM item_classes WHERE item_id = ?"
    db.execute(sql, [item_id])

    sql = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for title, value in classes:
        db.execute(sql, [item_id, title, value])

def remove_item(item_id):
    sql = "DELETE FROM item_classes WHERE item_id = ?"
    db.execute(sql, [item_id])

    sql = "DELETE FROM items WHERE id = ?"
    db.execute(sql, [item_id])

def find_items(query):
    sql = """SELECT id, title
             FROM items
             WHERE title LIKE ? OR description LIKE ?
             ORDER BY id DESC"""
    like = "%" + query + "%"
    return db.query(sql, [like, like])