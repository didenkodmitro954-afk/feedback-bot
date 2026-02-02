import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Таблиці
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY
)
""")

conn.commit()

# ---------------- Функції ----------------

def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def add_admin(admin_id):
