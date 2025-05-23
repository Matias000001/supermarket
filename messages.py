"""
This module handles operations related to messaging between users,
including retrieving conversations, sending messages, and deleting conversations.
"""

from flask import session
import db


def get_user_conversations(user_id):
    """Fetches a list of conversations for a given user."""
    sql = """WITH conversation_partners AS (
                 SELECT
                     CASE
                         WHEN sender_id = ? THEN recipient_id
                         ELSE sender_id
                     END AS partner_id,
                     MAX(sent_at) AS last_message_time
                 FROM messages
                 WHERE sender_id = ? OR recipient_id = ?
                 GROUP BY partner_id
             )
             SELECT
                 u.id AS partner_id,
                 u.username AS partner_name,
                 m.id AS message_id,
                 m.content,
                 datetime(m.sent_at) AS sent_at,
                 m.sender_id
             FROM conversation_partners cp
             JOIN users u ON cp.partner_id = u.id
             JOIN messages m ON (
                 (m.sender_id = ? AND m.recipient_id = cp.partner_id) OR
                 (m.sender_id = cp.partner_id AND m.recipient_id = ?)
             )
             ORDER BY cp.last_message_time DESC, m.sent_at ASC"""
    messages_data = db.query(sql, [user_id, user_id, user_id, user_id, user_id])
    conversations = {}
    for msg in messages_data:
        partner_id = msg["partner_id"]
        if partner_id not in conversations:
            conversations[partner_id] = {
                "partner_id": partner_id,
                "partner_name": msg["partner_name"],
                "messages": []
            }
        conversations[partner_id]["messages"].append({
            "id": msg["message_id"],
            "content": msg["content"],
            "sent_at": msg["sent_at"],
            "sender_id": msg["sender_id"]
        })
    return list(conversations.values())


def send_message(recipient_id, content):
    """Sends a message to a recipient and returns success status."""
    if "id" not in session:
        raise PermissionError("User is not logged in")
    sender_id = session["id"]
    sql = "INSERT INTO messages (content, sender_id, recipient_id) VALUES (?, ?, ?)"
    db.execute(sql, [content, sender_id, recipient_id])


def delete_conversation(partner_id):
    """Deletes all messages with a conversation partner and returns success status."""
    if "id" not in session:
        raise PermissionError("User is not logged in")
    user_id = session["id"]
    sql = """DELETE FROM messages
             WHERE (sender_id = ? AND recipient_id = ?) 
             OR (sender_id = ? AND recipient_id = ?)"""
    db.execute(sql, [user_id, partner_id, partner_id, user_id])


def get_conversation_between_users(user1_id, user2_id):
    """Fetches the conversation between two users as a list of messages."""
    sql = """SELECT m.id, m.content, datetime(m.sent_at) AS sent_at,
                    m.sender_id, u.username AS sender_name
             FROM messages m
             JOIN users u ON m.sender_id = u.id
             WHERE (m.sender_id = ? AND m.recipient_id = ?)
                OR (m.sender_id = ? AND m.recipient_id = ?)
             ORDER BY m.sent_at ASC"""
    messages_data = db.query(sql, [user1_id, user2_id, user2_id, user1_id])
    conversation = []
    for msg in messages_data:
        conversation.append({
            "id": msg["id"],
            "content": msg["content"],
            "sent_at": msg["sent_at"],
            "sender_id": msg["sender_id"],
            "sender_name": msg["sender_name"]
        })
    return conversation
