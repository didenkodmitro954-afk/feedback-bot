import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# ------------------ користувачі ------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    blocked INTEGER DEFAULT 0
)
""")

# ------------------ адміни ------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY
)
""")

# ------------------ лог дій адмінів ------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER,
    action TEXT,
    target_user INTEGER,
    info TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# ------------------ розіграші ------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaway_users (
    user_id INTEGER,
    giveaway_id INTEGER
)
""")

conn.commit()

# ------------------ Функції ------------------

# користувачі
def add_user(user_id, username):
    cursor.execute(
        "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()

def is_blocked(user_id):
    cursor.execute("SELECT blocked FROM users WHERE id=?", (user_id,))
    r = cursor.fetchone()
    return r and r[0] == 1

def block_user(user_id):
    cursor.execute("UPDATE users SET blocked=1 WHERE id=?", (user_id,))
    conn.commit()

def unblock_user(user_id):
    cursor.execute("UPDATE users SET blocked=0 WHERE id=?", (user_id,))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT id FROM users WHERE blocked=0")
    return [x[0] for x in cursor.fetchall()]

# адміни
def add_admin(admin_id):
    cursor.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (admin_id,))
    conn.commit()

def remove_admin(admin_id):
    cursor.execute("DELETE FROM admins WHERE id=?", (admin_id,))
    conn.commit()

def get_all_admins():
    cursor.execute("SELECT id FROM admins")
    return [x[0] for x in cursor.fetchall()]

# лог
def add_log(admin_id, action, target_user=None, info=""):
    cursor.execute(
        "INSERT INTO admin_logs (admin_id, action, target_user, info) VALUES (?, ?, ?, ?)",
        (admin_id, action, target_user, info)
    )
    conn.commit()

def get_logs():
    cursor.execute("SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT 50")
    return cursor.fetchall()

# розіграші
def create_giveaway(title):
    cursor.execute("INSERT INTO giveaways (title) VALUES (?)", (title,))
    conn.commit()

def join_giveaway(user_id, giveaway_id):
    cursor.execute(
        "INSERT INTO giveaway_users (user_id, giveaway_id) VALUES (?, ?)",
        (user_id, giveaway_id)
    )
    conn.commit()

def get_giveaways():
    cursor.execute("SELECT * FROM giveaways")
    return cursor.fetchall()
