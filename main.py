import asyncio
import logging
import sqlite3
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================== НАЛАШТУВАННЯ ==================
TOKEN = "8468725441:AAFTU2RJfOH3Eo__nJtEw1NqUbj5Eu3cTUE"
OWNER_USERNAME = "userveesna"  # ти — головний адмін

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================== БАЗА ДАНИХ ==================
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
    last_time INTEGER
)
""")

conn.commit()

cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (OWNER_USERNAME,))
conn.commit()

# ================== ФУНКЦІЇ ==================
def is_admin(username):
    cur.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    return cur.fetchone() is not None

def add_user(user_id, username):
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)",
        (user_id, username)
    )
    conn.commit()

def get_admins():
    cur.execute("SELECT username FROM admins")
    return [x[0] for x in cur.fetchall()]

def get_user_id(username):
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    r = cur.fetchone()
    return r[0] if r else None

def take_ticket(user_id, admin):
    cur.execute(
        "INSERT OR REPLACE INTO tickets VALUES (?,?,?)",
        (user_id, admin, int(time.time()))
    )
    conn.commit()

def get_ticket(user_id):
    cur.execute(
        "SELECT admin_username, last_time FROM tickets WHERE user_id=?",
        (user_id,)
    )
    return cur.fetchone()

def close_ticket(user_id):
    cur.execute("DELETE FROM tickets WHERE user_id=?", (user_id,))
    conn.commit()

# ================== /start ==================
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)

    await msg.answer(
        "👋 Вітаємо!\n\n"
        "✅ Ви успішно зареєстровані\n\n"
        "📨 Напишіть своє повідомлення — адміністрація відповість вам\n\n"
        "📌 Прайс-лист: https://t.me/praiceabn\n"
        "📣 Основний канал: https://t.me/reklamaabn"
    )

    cur.execute("SELECT notified FROM users WHERE user_id=?", (msg.from_user.id,))
    if cur.fetchone()[0] == 0:
        for admin in get_admins():
            uid = get_user_id(admin)
            if uid:
                await bot.send_message(
                    uid,
                    f"🆕 Новий користувач:\n"
                    f"👤 @{msg.from_user.username}\n"
                    f"🆔 {msg.from_user.id}"
                )
        cur.execute(
            "UPDATE users SET notified=1 WHERE user_id=?",
            (msg.from_user.id,)
        )
        conn.commit()

# ================== /ahelp ==================
@dp.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return

    await msg.answer(
        "⚙️ Адмін-команди:\n\n"
        "/ahelp — допомога\n"
        "/reply @user текст — відповісти та взяти тікет\n"
        "/closeticket @user — закрити тікет"
    )

# ================== /reply ==================
@dp.message(Command("reply"))
async def reply(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return

    try:
        _, username, text = msg.text.split(" ", 2)
        username = username.replace("@", "")
        user_id = get_user_id(username)

        if not user_id:
            await msg.answer("❌ Користувача не знайдено")
            return

        ticket = get_ticket(user_id)
        if ticket and ticket[0] != msg.from_user.username:
            await msg.answer("❌ Тікет вже взяв інший адмін")
            return

        take_ticket(user_id, msg.from_user.username)

        await bot.send_message(
            user_id,
            f"👮 Адміністратор відповів:\n\n{text}"
        )

        for admin in get_admins():
            uid = get_user_id(admin)
            if uid:
                await bot.send_message(
                    uid,
                    f"📌 Адмін @{msg.from_user.username} взяв тікет @{username}"
                )

        await msg.answer("✅ Відповідь надіслано")

    except:
        await msg.answer("❌ Формат: /reply @username текст")

# ================== /closeticket ==================
@dp.message(Command("closeticket"))
async def close_ticket_cmd(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return

    try:
        _, username = msg.text.split()
        username = username.replace("@", "")
        user_id = get_user_id(username)

        if not user_id:
            await msg.answer("❌ Користувача не знайдено")
            return

        close_ticket(user_id)

        await bot.send_message(
            user_id,
            "✅ Ваше звернення закрито.\n"
            "Можете написати знову, якщо потрібно."
        )
        await msg.answer("✅ Тікет закрито")

    except:
        await msg.answer("❌ Формат: /closeticket @username")

# ================== ПОВІДОМЛЕННЯ КОРИСТУВАЧА ==================
@dp.message()
async def user_message(msg: types.Message):
    if is_admin(msg.from_user.username):
        return

    await msg.answer("✅ Повідомлення надіслано адміністрації")

    ticket = get_ticket(msg.from_user.id)
    if ticket:
        admin, last = ticket
        if time.time() - last > 1800:
            close_ticket(msg.from_user.id)
            ticket = None

    for admin in get_admins():
        if ticket and admin != ticket[0]:
            continue

        uid = get_user_id(admin)
        if uid:
            await bot.send_message(
                uid,
                f"📩 @{msg.from_user.username}:\n{msg.text}"
            )

# ================== ЗАПУСК ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
