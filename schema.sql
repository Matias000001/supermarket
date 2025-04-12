CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    image BLOB
);

CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    price INTEGER,
    user_id INTEGER REFERENCES users,
    quantity INTEGER,
    image_filename TEXT
);

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

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
    sender_id INTEGER,
    recipient_id INTEGER,
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (recipient_id) REFERENCES users(id)
);

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