import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    days INTEGER,
    active INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS giveaway_users (
    giveaway_id INTEGER,
    user_id INTEGER
)
""")

conn.commit()


def add_admin(username):
    cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (username,))
    conn.commit()


def is_admin(username):
    cur.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    return cur.fetchone() is not None


def add_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (user_id, username))
    conn.commit()


def get_users():
    cur.execute("SELECT user_id FROM users")
    return [x[0] for x in cur.fetchall()]


def create_giveaway(title, days):
    cur.execute(
        "INSERT INTO giveaways (title, days, active) VALUES (?,?,1)",
        (title, days)
    )
    conn.commit()
    return cur.lastrowid


def get_active_giveaways():
    cur.execute("SELECT id, title FROM giveaways WHERE active=1")
    return cur.fetchall()


def join_giveaway(giveaway_id, user_id):
    cur.execute(
        "INSERT OR IGNORE INTO giveaway_users VALUES (?,?)",
        (giveaway_id, user_id)
    )
    conn.commit()
