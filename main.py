import asyncio
import logging
import sqlite3
import time
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================= НАСТРОЙКИ =================
TOKEN = "8511337609:AAFNtvQWoD4rhyYugouVgsspw0FKorm-rDM"
OWNER_USERNAME = "userveesna"  # головний адмін

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= БАЗА =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

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
CREATE TABLE IF NOT EXISTS tickets (
    user_id INTEGER PRIMARY KEY,
    admin_username TEXT,
    notified INTEGER,
    last_time INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    end_time INTEGER,
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
cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (OWNER_USERNAME,))
conn.commit()

# ================= ФУНКЦІЇ =================
def is_admin(username):
    cur.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    return cur.fetchone() is not None

def get_admins():
    cur.execute("SELECT username FROM admins")
    return [x[0] for x in cur.fetchall()]

def add_user(uid, username):
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
        (uid, username)
    )
    conn.commit()

def get_user_id(username):
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    r = cur.fetchone()
    return r[0] if r else None

def take_ticket(user_id, admin):
    cur.execute(
        "INSERT OR REPLACE INTO tickets VALUES (?,?,?,?)",
        (user_id, admin, 0, int(time.time()))
    )
    conn.commit()

def get_ticket(user_id):
    cur.execute(
        "SELECT admin_username, notified, last_time FROM tickets WHERE user_id=?",
        (user_id,)
    )
    return cur.fetchone()

def mark_ticket_notified(user_id):
    cur.execute("UPDATE tickets SET notified=1 WHERE user_id=?", (user_id,))
    conn.commit()

def close_ticket(user_id):
    cur.execute("DELETE FROM tickets WHERE user_id=?", (user_id,))
    conn.commit()

def create_giveaway(title, days):
    end_time = int(time.time()) + days * 86400
    cur.execute(
        "INSERT INTO giveaways (title, end_time, active) VALUES (?,?,1)",
        (title, end_time)
    )
    conn.commit()
    gid = cur.lastrowid
    # Додаємо автоматичне завершення розіграшу
    asyncio.create_task(finish_giveaway(gid, end_time))
    return gid, end_time

def close_giveaway(gid):
    cur.execute("UPDATE giveaways SET active=0 WHERE id=?", (gid,))
    conn.commit()

def get_active_giveaways():
    cur.execute("SELECT id, title FROM giveaways WHERE active=1")
    return cur.fetchall()

def join_giveaway(gid, user_id):
    cur.execute(
        "INSERT OR IGNORE INTO giveaway_users VALUES (?,?)",
        (gid, user_id)
    )
    conn.commit()

# ================= Функція завершення розіграшу =================
async def finish_giveaway(gid, end_time):
    await asyncio.sleep(max(0, end_time - time.time()))
    cur.execute("SELECT user_id FROM giveaway_users WHERE giveaway_id=?", (gid,))
    users = cur.fetchall()
    close_giveaway(gid)
    if not users:
        # Якщо учасників немає
        for admin in get_admins():
            uid = get_user_id(admin)
            if uid:
                await bot.send_message(uid, f"⚠️ Розіграш ID {gid} завершено — учасників немає")
        return

    winner = random.choice(users)[0]
    for admin in get_admins():
        uid = get_user_id(admin)
        if uid:
            await bot.send_message(uid, f"🏆 Переможець розіграшу ID {gid}:\n🆔 {winner}")

# ================= /start =================
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)
    await msg.answer(
        "👋 Вітаємо!\n\n"
        "✅ Ви успішно зареєстровані\n\n"
        "✉️ Напишіть повідомлення — адміністрація відповість\n\n"
        "💰 Прайс-лист: https://t.me/praiceabn\n"
        "📣 Основний канал: https://t.me/reklamaabn"
    )

    cur.execute("SELECT notified FROM users WHERE user_id=?", (msg.from_user.id,))
    if cur.fetchone()[0] == 0:
        for admin in get_admins():
            uid = get_user_id(admin)
            if uid:
                await bot.send_message(uid, f"🆕 Новий користувач:\n👤 @{msg.from_user.username}\n🆔 {msg.from_user.id}")
        cur.execute("UPDATE users SET notified=1 WHERE user_id=?", (msg.from_user.id,))
        conn.commit()

# ================= /ahelp =================
@dp.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    await msg.answer(
        "⚙️ Адмін-команди:\n"
        "/take @user — взяти тікет\n"
        "/reply @user текст — відповісти у взятому тікеті\n"
        "/closeticket @user — закрити тікет\n"
        "/creategiveaway Назва | дні — створити розіграш\n"
        "/delgiveaway ID — закрити розіграш\n"
        "/giveaways — активні розіграші\n"
        "/a — адмін-чат\n"
        "/o текст — оголошення усім користувачам\n"
        "/addadmin @user (тільки GA)\n"
        "/deladmin @user (тільки GA)"
    )

# ================= Решта коду залишається без змін =================
# /take, /reply, /closeticket, /a, /o, /addadmin, /deladmin, /user_msg
# (копіюй усе зі свого останнього робочого коду)
# Тільки додати finish_giveaway у create_giveaway
# ================= Запуск =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
