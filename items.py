import db

def get_all_classes():
    sql = "SELECT DISTINCT title, value FROM classes ORDER BY id"
    result = db.query(sql)
    classes = {}
    for title, value in result:
        classes.setdefault(title, []).append(value)
    return classes

def add_item(title, description, price, quantity, user_id, classes, image_filename=None):
    sql = "INSERT INTO items (title, description, price, quantity, user_id, image_filename) VALUES (?, ?, ?, ?, ?, ?)"
    db.execute(sql, [title, description, price, quantity, user_id, image_filename])
    item_id = db.last_insert_id()

    sql = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for title, value in classes:
        db.execute(sql, [item_id, title, value])

def add_purchase(item_id, user_id, seller_id, price, quantity):
    sql = """INSERT INTO purchases (item_id, user_id, quantity, price_at_purchase, seller_id) 
             VALUES (?, ?, ?, ?, ?)"""
    db.execute(sql, [item_id, user_id, quantity, price, seller_id])

def get_purchases(user_id):
    sql = """SELECT p.id AS purchase_id, i.title AS item_title, p.quantity, p.price_at_purchase,
                    (p.quantity * p.price_at_purchase) AS total_price, i.image_filename
                    FROM purchases p
                    LEFT JOIN items i ON p.item_id = i.id
                    WHERE p.user_id = ? AND p.status = 'pending'"""
    return db.query(sql, [user_id])

def get_user_items(user_id):
    sql = "SELECT id, title, quantity, image_filename FROM items WHERE user_id = ? ORDER BY id DESC"
    return db.query(sql, [user_id])

def get_classes(item_id):
    sql = """SELECT title, value 
                    FROM item_classes
                    WHERE item_id = ?"""
    return db.query(sql, [item_id])

def get_item(item_id):
    sql = """SELECT i.id, i.title, i.description, i.price, i.quantity,
                    u.id AS user_id, u.username, i.image_filename
                    FROM items i
                    JOIN users u ON i.user_id = u.id
                    WHERE i.id = ?"""
    result = db.query(sql, [item_id])
    return result[0] if result else None

def update_item(item_id, title, description, classes, quantity, image_filename=None):
    sql = "UPDATE items SET title=?, description=?, quantity=?, image_filename=? WHERE id=?"
    db.execute(sql, [title, description, quantity, image_filename, item_id])
    
    sql = "DELETE FROM item_classes WHERE item_id=?"
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

def items_count():
    sql = "SELECT COUNT(*) FROM items"
    result = db.query(sql)
    return result[0][0] if result else 0

def get_items(page, page_size):
    sql = """SELECT i.id, i.title, i.description, i.price, i.quantity, u.id AS user_id, u.username, i.image_filename
             FROM items i
             JOIN users u ON i.user_id = u.id
             ORDER BY i.id DESC
             LIMIT ? OFFSET ?"""
    limit = page_size
    offset = page_size * (page - 1)
    return db.query(sql, [limit, offset])