import db

def update_quantity(purchase_id, user_id, quantity):
    sql = "UPDATE purchases SET quantity = ? WHERE id = ? AND user_id = ?"
    db.execute(sql, [quantity, purchase_id, user_id])

def remove_item(purchase_id, user_id):
    sql = "DELETE FROM purchases WHERE id = ? AND user_id = ?"
    db.execute(sql, [purchase_id, user_id])

def get_cart(user_id):
    sql = """SELECT p.id AS purchase_id, i.id AS item_id, i.title, p.quantity, p.price_at_purchase,
                    (p.quantity * p.price_at_purchase) AS total_price
             FROM purchases p
             JOIN items i ON p.item_id = i.id
             WHERE p.user_id = ? AND p.status = 'pending'"""
    return db.query(sql, [user_id])

def checkout(user_id):
    sql = "UPDATE purchases SET status = 'paid' WHERE user_id = ? AND status = 'pending'"
    db.execute(sql, [user_id])

def get_quantitys(product_ids):
    sql = """SELECT id, quantity FROM items WHERE id IN ({})""".format(','.join(['?'] * len(product_ids)))
    return db.query(sql, product_ids)