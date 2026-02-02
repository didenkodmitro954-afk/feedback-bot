import sqlite3

# Підключення до бази (створиться, якщо нема)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Створюємо таблицю користувачів
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0
)
""")
conn.commit()

def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def update_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    conn.commit()
