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
    username TEXT,
    notified INTEGER DEFAULT 0
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY
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

def get_users():
    cur.execute("SELECT user_id FROM users")
    return [x[0] for x in cur.fetchall()]

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

def create_giveaway(title, days):
    cur.execute("INSERT INTO giveaways (title, days, active) VALUES (?,?,1)", (title, days))
    conn.commit()
    return cur.lastrowid

def get_active_giveaways():
    cur.execute("SELECT id, title FROM giveaways WHERE active=1")
    return cur.fetchall()

def join_giveaway(giveaway_id, user_id):
    cur.execute("INSERT OR IGNORE INTO giveaway_users VALUES (?,?)", (giveaway_id, user_id))
    conn.commit()

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

def get_admins():
    cur.execute("SELECT username FROM admins")
    return [x[0] for x in cur.fetchall()]

# ---------------- Команди користувачів ----------------
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)
    welcome_text = (
        f"🎉 Привіт, @{msg.from_user.username}! 🎉\n\n"
        "🌟 Ласкаво просимо до нашої спільноти.\n"
        "💰 Ознайомитися з прайс листом: https://t.me/praiceabn\n"
        "📣 Основний канал: https://t.me/reklamaabn\n\n"
        "🎁 Ви можете приєднатися до розіграшів:\n"
        "👉 Переглянути активні: /giveaways\n"
        "👉 Приєднатися до конкретного: /join<ID>\n\n"
        "💬 Створіть тікет для зв'язку з адміном: /ticket Ваше повідомлення"
    )
    await msg.answer(welcome_text)

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
                                               f"👤 Username: @{username}\n"
                                               f"🆔 ID: {user_id}")
                    except: pass
        mark_notified(user_id)

@dp.message(Command("giveaways"))
async def giveaways(msg: types.Message):
    gvs = get_active_giveaways()
    if not gvs:
        await msg.answer("❌ Немає активних розіграшів.")
        return
    text = "🎁 Активні розіграші:\n"
    for g in gvs:
        text += f"\nID {g[0]} — {g[1]} /join{g[0]}"
    await msg.answer(text)

@dp.message(lambda m: m.text.startswith("/join"))
async def join(msg: types.Message):
    try:
        gid = int(msg.text.replace("/join", ""))
        join_giveaway(gid, msg.from_user.id)
        await msg.answer("✅ Ви приєдналися до розіграшу!")
    except:
        await msg.answer("❌ Невірна команда. Використання: /join<ID>")

# ---------------- Тікети ----------------
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
    await msg.answer("✅ Ваш тікет відкрито! Адміністратори отримали повідомлення. Ви можете писати сюди без команд, поки тікет не буде закрито.")

    for admin in get_admins():
        cur.execute("SELECT user_id FROM users WHERE username=?", (admin,))
        res = cur.fetchone()
        if res:
            admin_id = res[0]
            try:
                await bot.send_message(admin_id,
                                       f"📩 Нова заявка від @{msg.from_user.username}:\n{text}\n"
                                       f"➡️ Ви можете вести тікет, поки він відкритий.")
            except: pass

@dp.message(lambda m: True)
async def handle_ticket_messages(msg: types.Message):
    if ticket_exists(msg.from_user.username):
        # повідомлення користувача адмінам
        admin = get_ticket_admin(msg.from_user.username)
        if admin:
            cur.execute("SELECT user_id FROM users WHERE username=?", (admin,))
            res = cur.fetchone()
            if res:
                admin_id = res[0]
                await bot.send_message(admin_id, f"💬 @{msg.from_user.username}: {msg.text}")
        else:
            for admin in get_admins():
                cur.execute("SELECT user_id FROM users WHERE username=?", (admin,))
                res = cur.fetchone()
                if res:
                    admin_id = res[0]
                    await bot.send_message(admin_id, f"💬 @{msg.from_user.username}: {msg.text}")
        return
    if is_admin(msg.from_user.username):
        cur.execute("SELECT username FROM tickets WHERE admin=?", (msg.from_user.username,))
        tickets = cur.fetchall()
        for t in tickets:
            username = t[0]
            cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
            res = cur.fetchone()
            if res:
                user_id = res[0]
                await bot.send_message(user_id, f"💬 Адміністратор: {msg.text}")

# ---------------- Адмінські команди ----------------
@dp.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    text = (
        "⚙️ Команди адміністратора:\n"
        "/ahelp — список команд\n"
        "/addadmin @username — додати адміна\n"
        "/deladmin @username — видалити адміна\n"
        "/take @username — взяти тікет\n"
        "/close_ticket @username — закрити тікет\n"
        "/creategiveaway Назва | дні — створити розіграш\n"
        "/giveaways — активні розіграші"
    )
    await msg.answer(text)

@dp.message(Command("addadmin"))
async def add_admin_command(msg: types.Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    try:
        username = msg.text.split()[1].replace("@", "")
        add_admin(username)
        await msg.answer(f"✅ @{username} доданий як адмін")
    except:
        await msg.answer("❌ Використання: /addadmin @username")

@dp.message(Command("deladmin"))
async def del_admin_command(msg: types.Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    try:
        username = msg.text.split()[1].replace("@", "")
        del_admin(username)
        await msg.answer(f"✅ @{username} видалений з адмінів")
    except:
        await msg.answer("❌ Використання: /deladmin @username")

# ---------------- Запуск ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
