import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# ---------------- Таблиці ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    creator TEXT,
    end_time INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaway_users (
    username TEXT,
    giveaway_id INTEGER,
    UNIQUE(username, giveaway_id)
)
""")

conn.commit()

# ---------------- Функції ----------------

# Користувачі
def add_user(username):
    cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()

def get_all_users():
    cursor.execute("SELECT username FROM users")
    return [x[0] for x in cursor.fetchall()]

# Адміни
def add_admin(username):
    cursor.execute("INSERT OR IGNORE INTO admins (username) VALUES (?)", (username,))
    conn.commit()

def remove_admin(username):
    cursor.execute("DELETE FROM admins WHERE username=?", (username,))
    conn.commit()

def get_all_admins():
    cursor.execute("SELECT username FROM admins")
    return [x[0] for x in cursor.fetchall()]

# Розіграші
def create_giveaway(title, creator, end_time):
    cursor.execute("INSERT INTO giveaways (title, creator, end_time) VALUES (?, ?, ?)", (title, creator, end_time))
    conn.commit()
    return cursor.lastrowid

def get_giveaways():
    cursor.execute("SELECT * FROM giveaways")
    return cursor.fetchall()

def get_giveaway_by_id(gid):
    cursor.execute("SELECT * FROM giveaways WHERE id=?", (gid,))
    return cursor.fetchone()

def join_giveaway(username, giveaway_id):
    try:
        cursor.execute("INSERT INTO giveaway_users (username, giveaway_id) VALUES (?, ?)", (username, giveaway_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

def get_giveaway_participants(giveaway_id):
    cursor.execute("SELECT username FROM giveaway_users WHERE giveaway_id=?", (giveaway_id,))
    return [x[0] for x in cursor.fetchall()]
