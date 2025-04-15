"""
This module handles user-related operations like creating a user,
validating login, updating profile images, and retrieving user data
from the database.
"""

from werkzeug.security import generate_password_hash, check_password_hash
import db


def create_user(username, password):
    """Creates a new user and stores the hashed password in the database."""
    password_hash = generate_password_hash(password)
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    db.execute(sql, [username, password_hash])


def check_login(username, password):
    """Validates user login and returns user ID if successful, otherwise None."""
    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])
    if not result:
        return None
    user_id = result[0]["id"]
    password_hash = result[0]["password_hash"]
    if check_password_hash(password_hash, password):
        return user_id
    return None


def update_image(user_id, image):
    """Updates a user's profile image with new image data."""
    sql = "UPDATE users SET image = ? WHERE id = ?"
    db.execute(sql, [image, user_id])


def get_user(user_id):
    """Fetches user data by ID, or returns None if not found."""
    sql = """SELECT id, username, image IS NOT NULL as has_image
             FROM users
             WHERE id = ?"""
    result = db.query(sql, [user_id])
    return result[0] if result else None


def get_image(user_id):
    """Retrieves image data for a given user ID, or None if not found."""
    sql = "SELECT image FROM users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0][0] if result else None
