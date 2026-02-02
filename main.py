import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import sqlite3
from datetime import datetime

TOKEN = "8468725441:AAFTU2RJfOH3Eo__nJtEw1NqUbj5Eu3cTUE"
OWNER_USERNAME = "userveesna"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ---
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# таблиці користувачів та адмінів
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
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

# Додаємо головного адміна
cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (OWNER_USERNAME,))
conn.commit()

# --- ФУНКЦІЇ ---
def add_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (user_id, username))
    conn.commit()

def mark_notified(username):
    cur.execute("UPDATE users SET notified=1 WHERE username=?", (username,))
    conn.commit()

def was_notified(username):
    cur.execute("SELECT notified FROM users WHERE username=?", (username,))
    res = cur.fetchone()
    return res[0] == 1 if res else False

def is_admin(username):
    cur.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    return cur.fetchone() is not None

def get_admins():
    cur.execute("SELECT username FROM admins")
    return [row[0] for row in cur.fetchall()]

def get_user_id(username):
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    res = cur.fetchone()
    return res[0] if res else None

def add_admin(username):
    cur.execute("INSERT OR IGNORE INTO admins (username) VALUES (?)", (username,))
    conn.commit()

def del_admin(username):
    cur.execute("DELETE FROM admins WHERE username=?", (username,))
    conn.commit()

# --- START ---
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)

    welcome_text = (
        f"🎉 Привіт, @{msg.from_user.username}! 🎉\n\n"
        "🌟 Ласкаво просимо до нашої спільноти.\n"
        "💰 Ознайомитися з прайс листом: https://t.me/praiceabn\n"
        "📣 Основний канал: https://t.me/reklamaabn\n\n"
        "💬 Надішліть повідомлення сюди, і наші адміністратори обов’язково зв’яжуться з вами!"
    )
    await msg.answer(welcome_text)

    # Повідомлення адмінам один раз
    if not was_notified(msg.from_user.username):
        for admin_username in get_admins():
            try:
                await bot.send_message(
                    chat_id=f"@{admin_username}",
                    text=(
                        f"🆕 Новий користувач зареєстрований!\n"
                        f"👤 Username: @{msg.from_user.username}\n"
                        f"🆔 ID: {msg.from_user.id}\n"
                        f"⏰ Зареєстрований: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    )
                )
            except Exception as e:
                print(f"Помилка відправки адміну {admin_username}: {e}")
        mark_notified(msg.from_user.username)

# --- АДМІН-КОМАНДИ ---
@dp.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    await msg.answer(
        "⚙️ Команди адміністратора:\n"
        "/ahelp — список команд\n"
        "/addadmin @username — додати адміна\n"
        "/deladmin @username — видалити адміна\n"
        "/reply @username Текст — відповісти користувачу"
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

@dp.message(Command("reply"))
async def reply(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        parts = msg.text.split(" ", 2)
        username = parts[1].replace("@", "")
        reply_text = parts[2]
        user_id = get_user_id(username)
        if user_id:
            await bot.send_message(user_id, f"💬 Відповідь адміністратора:\n\n{reply_text}")
            await msg.answer(f"✅ Повідомлення надіслано @{username}")
        else:
            await msg.answer("❌ Користувач не знайдений")
    except:
        await msg.answer("❌ Використання: /reply @username Текст")

# --- ЗВОРОТНИЙ ЗВ'ЯЗОК ВІД КОРИСТУВАЧА ---
@dp.message()
async def feedback(msg: types.Message):
    if is_admin(msg.from_user.username):
        return
    add_user(msg.from_user.id, msg.from_user.username)
    # Повідомлення всім адмінам по username
    for admin_username in get_admins():
        try:
            await bot.send_message(
                chat_id=f"@{admin_username}",
                text=f"📩 Нове повідомлення від @{msg.from_user.username}:\n\n{msg.text}"
            )
        except: pass
    await msg.answer("💌 Ваше повідомлення отримано! Адміністратор незабаром відповість.")

# --- ЗАПУСК ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
