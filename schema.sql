CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    image BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);


CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL CHECK(price >= 0),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity >= 0),
    image BLOB,
    FOREIGN KEY (user_id) REFERENCES users(id)
);


CREATE INDEX idx_items_title ON items(title);
CREATE INDEX idx_items_user_id ON items(user_id);
CREATE INDEX idx_items_created_at ON items(created_at);


CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    value TEXT
);


CREATE TABLE item_classes (
    id INTEGER PRIMARY KEY,
    item_id INTEGER REFERENCES items,
    title TEXT,
    value TEXT
);

CREATE INDEX idx_item_classes_item_id ON item_classes(item_id);
CREATE INDEX idx_item_classes_title_value ON item_classes(title, value);


CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
    sender_id INTEGER,
    recipient_id INTEGER,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (recipient_id) REFERENCES users(id)
);

CREATE INDEX idx_messages_sender_id ON messages(sender_id);
CREATE INDEX idx_messages_recipient_id ON messages(recipient_id);
CREATE INDEX idx_messages_sent_at ON messages(sent_at);


CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER REFERENCES items,
    user_id INTEGER REFERENCES users,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price_at_purchase INTEGER NOT NULL,
    purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK (status IN ('pending', 'paid', 'shipped', 'delivered')) DEFAULT 'pending',
    seller_id INTEGER REFERENCES users(id)
);

CREATE INDEX idx_purchases_item_id ON purchases(item_id);
CREATE INDEX idx_purchases_user_id ON purchases(user_id);
CREATE INDEX idx_purchases_seller_id ON purchases(seller_id);
CREATE INDEX idx_purchases_purchased_at ON purchases(purchased_at);


CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_item_id ON comments(item_id);
