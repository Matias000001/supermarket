import db

def add_item(title, description, price, user_id):
    sql = """INSERT INTO items (title, description, price, user_id) 
          VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, description, price, user_id])