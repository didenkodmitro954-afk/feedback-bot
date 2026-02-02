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
conn.commit()

# Головний адмін
cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (OWNER_USERNAME,))
conn.commit()

# ---------------- Функції ----------------
def add_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (user_id, username))
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

def get_user_id(username):
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    res = cur.fetchone()
    return res[0] if res else None

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)
    welcome_text = (
        f"🎉 Привіт, @{msg.from_user.username}! 🎉\n\n"
        "🌟 Ласкаво просимо до нашої спільноти.\n"
        "💰 Ознайомитися з прайс листом: https://t.me/praiceabn\n"
        "📣 Основний канал: https://t.me/reklamaabn\n\n"
        "💬 Ви можете написати повідомлення у будь-який час, і наші адміністратори зв’яжуться з вами."
    )
    await msg.answer(welcome_text)

# ---------------- ЗВОРОТНИЙ ЗВ'ЯЗОК ----------------
@dp.message()
async def feedback(msg: types.Message):
    if is_admin(msg.from_user.username):
        # Адміністратор пише — нічого не робимо
        return

    # Користувач написав повідомлення
    await msg.answer("✅ Ваше повідомлення отримано! Очікуйте відповіді адміністратора.")

    # Надсилаємо всім адмінам
    for admin in get_admins():
        admin_id = get_user_id(admin)
        if admin_id:
            try:
                await bot.send_message(admin_id,
                                       f"📩 Нове повідомлення від @{msg.from_user.username}:\n\n{msg.text}")
            except: 
                pass

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

# ---------------- ЗАПУСК ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
