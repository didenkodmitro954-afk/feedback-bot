import sqlite3

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# Користувачі
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    blocked INTEGER DEFAULT 0
)
""")

# Розіграші
cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT
)
""")

# Учасники розіграшів
cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaway_users (
    user_id INTEGER,
    giveaway_id INTEGER
)
""")

conn.commit()


def add_user(user_id, username):
    cursor.execute(
        "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()


def block_user(user_id):
    cursor.execute("UPDATE users SET blocked=1 WHERE id=?", (user_id,))
    conn.commit()


def unblock_user(user_id):
    cursor.execute("UPDATE users SET blocked=0 WHERE id=?", (user_id,))
    conn.commit()


def is_blocked(user_id):
    cursor.execute("SELECT blocked FROM users WHERE id=?", (user_id,))
    r = cursor.fetchone()
    return r and r[0] == 1


def get_all_users():
    cursor.execute("SELECT id FROM users WHERE blocked=0")
    return [x[0] for x in cursor.fetchall()]


def create_giveaway(title):
    cursor.execute("INSERT INTO giveaways (title) VALUES (?)", (title,))
    conn.commit()


def join_giveaway(user_id, giveaway_id):
    cursor.execute(
        "INSERT INTO giveaway_users (user_id, giveaway_id) VALUES (?, ?)",
        (user_id, giveaway_id)
    )
    conn.commit()
