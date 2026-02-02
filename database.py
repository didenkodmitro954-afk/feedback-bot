import sqlite3

# Підключення до бази
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# ---------------- Таблиці ----------------
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS giveaway_users (
    user_id INTEGER,
    giveaway_id INTEGER,
    UNIQUE(user_id, giveaway_id)
)
""")

conn.commit()

# ---------------- Функції ----------------

# Користувачі
def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

# Адміни
def add_admin(admin_id):
    cursor.execute("INSERT OR IGNORE INTO admins (id) VALUES (?)", (admin_id,))
    conn.commit()

def remove_admin(admin_id):
    cursor.execute("DELETE FROM admins WHERE id=?", (admin_id,))
    conn.commit()

def get_all_admins():
    cursor.execute("SELECT id FROM admins")
    return [x[0] for x in cursor.fetchall()]

# ---------------- Розіграші ----------------
def create_giveaway(title):
    cursor.execute("INSERT INTO giveaways (title) VALUES (?)", (title,))
    conn.commit()

def get_giveaways():
    cursor.execute("SELECT * FROM giveaways")
    return cursor.fetchall()

def join_giveaway(user_id, giveaway_id):
    try:
        cursor.execute("INSERT INTO giveaway_users (user_id, giveaway_id) VALUES (?, ?)", (user_id, giveaway_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # вже приєднався

def get_giveaway_participants(giveaway_id):
    cursor.execute("SELECT user_id FROM giveaway_users WHERE giveaway_id=?", (giveaway_id,))
    return [x[0] for x in cursor.fetchall()]
