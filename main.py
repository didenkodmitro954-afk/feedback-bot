import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import sqlite3

# ---------------- Налаштування ----------------
TOKEN = "8468725441:AAFTU2RJfOH3Eo__nJtEw1NqUbj5Eu3cTUE"
OWNER_USERNAME = "userveesna"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- База ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# Таблиці
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    notified INTEGER DEFAULT 0
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS tickets (
    username TEXT PRIMARY KEY,
    admin TEXT
)
""")
conn.commit()

# Головний адмін
cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (OWNER_USERNAME,))
conn.commit()

# ---------------- Функції ----------------
def add_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (user_id, username))
    conn.commit()

def get_new_users():
    cur.execute("SELECT user_id, username FROM users WHERE notified=0")
    return cur.fetchall()

def mark_notified(user_id):
    cur.execute("UPDATE users SET notified=1 WHERE user_id=?", (user_id,))
    conn.commit()

def add_admin(username):
    cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (username,))
    conn.commit()

def del_admin(username):
    cur.execute("DELETE FROM admins WHERE username=?", (username,))
    conn.commit()

def is_admin(username):
    cur.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    return cur.fetchone() is not None

def get_admins():
    cur.execute("SELECT username FROM admins")
    return [x[0] for x in cur.fetchall()]

def ticket_exists(username):
    cur.execute("SELECT 1 FROM tickets WHERE username=?", (username,))
    return cur.fetchone() is not None

def create_ticket(username):
    cur.execute("INSERT OR IGNORE INTO tickets (username, admin) VALUES (?,NULL)", (username,))
    conn.commit()

def get_ticket_admin(username):
    cur.execute("SELECT admin FROM tickets WHERE username=?", (username,))
    res = cur.fetchone()
    return res[0] if res else None

def assign_ticket(username, admin):
    cur.execute("UPDATE tickets SET admin=? WHERE username=?", (admin, username))
    conn.commit()

def close_ticket(username):
    cur.execute("DELETE FROM tickets WHERE username=?", (username,))
    conn.commit()

# ---------------- КОМАНДА START ----------------
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)
    welcome_text = (
        f"🎉 Привіт, @{msg.from_user.username}! 🎉\n\n"
        "🌟 Ласкаво просимо до нашої спільноти.\n"
        "💰 Ознайомитися з прайс листом: https://t.me/praiceabn\n"
        "📣 Основний канал: https://t.me/reklamaabn\n\n"
        "💬 Для звернення до адміністратора створіть тікет:\n"
        "/ticket Ваше повідомлення"
    )
    await msg.answer(welcome_text)

    # Повідомлення адмінам про нового користувача
    new_users = get_new_users()
    for user_id, username in new_users:
        for admin in get_admins():
            cur.execute("SELECT user_id FROM users WHERE username=?", (admin,))
            res = cur.fetchone()
            if res:
                admin_id = res[0]
                if admin_id != user_id:
                    try:
                        await bot.send_message(admin_id,
                                               f"🆕 Новий користувач зареєстрований!\n"
                                               f"👤 @{username}")
                    except: pass
        mark_notified(user_id)

# ---------------- ТІКЕТ ----------------
@dp.message(lambda m: m.text.startswith("/ticket"))
async def ticket(msg: types.Message):
    text = msg.text.replace("/ticket", "").strip()
    if not text:
        await msg.answer("❌ Напишіть повідомлення після /ticket")
        return
    if ticket_exists(msg.from_user.username):
        await msg.answer("⚠️ У вас вже є активний тікет")
        return
    create_ticket(msg.from_user.username)
    await msg.answer("✅ Ваш тікет відкрито! Ви можете писати сюди без команд, поки тікет не буде закрито.")

    # Повідомлення всім адмінам
    for admin in get_admins():
        cur.execute("SELECT user_id FROM users WHERE username=?", (admin,))
        res = cur.fetchone()
        if res:
            admin_id = res[0]
            try:
                await bot.send_message(admin_id,
                                       f"📩 Нова заявка від @{msg.from_user.username}:\n{text}")
            except: pass

# ---------------- ВІЛЬНИЙ ЧАТ ----------------
@dp.message()
async def free_ticket_chat(msg: types.Message):
    username = msg.from_user.username

    # Користувач пише у тікет
    if ticket_exists(username):
        admin = get_ticket_admin(username)
        if admin:
            cur.execute("SELECT user_id FROM users WHERE username=?", (admin,))
            res = cur.fetchone()
            if res:
                await bot.send_message(res[0], f"💬 @{username}: {msg.text}")
        else:
            # Якщо ще ніхто не взяв, надсилаємо всім адмінам
            for admin in get_admins():
                cur.execute("SELECT user_id FROM users WHERE username=?", (admin,))
                res = cur.fetchone()
                if res:
                    await bot.send_message(res[0], f"💬 @{username}: {msg.text}")
        return

    # Адмін пише у тікет
    if is_admin(username):
        cur.execute("SELECT username FROM tickets WHERE admin=?", (username,))
        tickets = cur.fetchall()
        for t in tickets:
            u_name = t[0]
            cur.execute("SELECT user_id FROM users WHERE username=?", (u_name,))
            res = cur.fetchone()
            if res:
                await bot.send_message(res[0], f"💬 Адміністратор: {msg.text}")

# ---------------- АДМІН КОМАНДИ ----------------
@dp.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    await msg.answer(
        "⚙️ Команди адміністратора:\n"
        "/ahelp — список команд\n"
        "/addadmin @username — додати адміна\n"
        "/deladmin @username — видалити адміна\n"
        "/take @username — взяти тікет\n"
        "/close_ticket @username — закрити тікет\n"
    )

@dp.message(Command("addadmin"))
async def add_admin_cmd(msg: types.Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    try:
        username = msg.text.split()[1].replace("@", "")
        add_admin(username)
        await msg.answer(f"✅ @{username} доданий як адмін")
    except:
        await msg.answer("❌ Використання: /addadmin @username")

@dp.message(Command("deladmin"))
async def del_admin_cmd(msg: types.Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    try:
        username = msg.text.split()[1].replace("@", "")
        del_admin(username)
        await msg.answer(f"✅ @{username} видалений з адмінів")
    except:
        await msg.answer("❌ Використання: /deladmin @username")

@dp.message(Command("close_ticket"))
async def close_ticket_cmd(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        username = msg.text.split()[1].replace("@", "")
        if not ticket_exists(username):
            await msg.answer("❌ Тікет не знайдено")
            return
        close_ticket(username)
        await msg.answer(f"✅ Тікет @{username} закрито")
        cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
        res = cur.fetchone()
        if res:
            await bot.send_message(res[0], "❌ Ваш тікет закрито адміністратором")
    except:
        await msg.answer("❌ Використання: /close_ticket @username")

# ---------------- ЗАПУСК ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
