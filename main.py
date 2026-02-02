import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import sqlite3
from datetime import datetime, timedelta
import random

# ---------------- Налаштування ----------------
TOKEN = "8468725441:AAFTU2RJfOH3Eo__nJtEw1NqUbj5Eu3cTUE"
OWNER_USERNAME = "userveesna"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- База ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# Користувачі та адміністратори
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY
)
""")
# Розіграші
cur.execute("""
CREATE TABLE IF NOT EXISTS raffles (
    raffle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    end_time TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS raffle_participants (
    raffle_id INTEGER,
    username TEXT
)
""")
conn.commit()

# Додаємо головного адміна
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
        "💬 Надішліть повідомлення сюди, і наші адміністратори обов'язково зв’яжуться з вами!"
    )
    await msg.answer(welcome_text)

# ---------------- ЗВОРОТНИЙ ЗВ'ЯЗОК ----------------
@dp.message()
async def feedback(msg: types.Message):
    if is_admin(msg.from_user.username):
        return  # адміністратор пише — нічого не робимо
    # повідомлення користувачем
    await msg.answer("✅ Ваше повідомлення отримано! Очікуйте відповіді адміністратора.")
    for admin in get_admins():
        admin_id = get_user_id(admin)
        if admin_id:
            try:
                await bot.send_message(admin_id,
                                       f"📩 Нове повідомлення від @{msg.from_user.username}:\n\n{msg.text}")
            except: pass

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
        "/createraffle Назва | Опис | Кількість днів — створити розіграш\n"
        "/joinraffle <raffle_id> — приєднатися до розіграшу (для користувачів)\n"
        "/closeraffle <raffle_id> — закрити розіграш та оголосити переможця\n"
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

# ---------------- РОЗІГРАШ ----------------
@dp.message(Command("createraffle"))
async def create_raffle(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        content = msg.text.replace("/createraffle", "").strip()
        name, description, days = [x.strip() for x in content.split("|")]
        end_time = (datetime.now() + timedelta(days=int(days))).isoformat()
        cur.execute("INSERT INTO raffles (name, description, end_time) VALUES (?,?,?)",
                    (name, description, end_time))
        raffle_id = cur.lastrowid
        conn.commit()
        await msg.answer(f"✅ Розіграш створено! ID: {raffle_id}\n{description}")
        # Повідомлення всім користувачам
        cur.execute("SELECT user_id FROM users")
        for user_id, in cur.fetchall():
            await bot.send_message(user_id,
                                   f"🎉 Новий розіграш!\nID: {raffle_id}\n{name}\n{description}\n"
                                   f"Приєднатися: /joinraffle {raffle_id}")
    except:
        await msg.answer("❌ Використання: /createraffle Назва | Опис | Кількість днів")

@dp.message(Command("joinraffle"))
async def join_raffle(msg: types.Message):
    try:
        raffle_id = int(msg.text.split()[1])
        username = msg.from_user.username
        cur.execute("INSERT OR IGNORE INTO raffle_participants (raffle_id, username) VALUES (?,?)",
                    (raffle_id, username))
        conn.commit()
        await msg.answer(f"✅ Ви приєдналися до розіграшу {raffle_id}")
    except:
        await msg.answer("❌ Використання: /joinraffle <raffle_id>")

@dp.message(Command("closeraffle"))
async def close_raffle(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        raffle_id = int(msg.text.split()[1])
        cur.execute("SELECT username FROM raffle_participants WHERE raffle_id=?", (raffle_id,))
        participants = [x[0] for x in cur.fetchall()]
        if not participants:
            await msg.answer("❌ Учасників немає")
            return
        winner = random.choice(participants)
        cur.execute("DELETE FROM raffles WHERE raffle_id=?", (raffle_id,))
        cur.execute("DELETE FROM raffle_participants WHERE raffle_id=?", (raffle_id,))
        conn.commit()
        await msg.answer(f"🏆 Розіграш {raffle_id} завершено! Переможець: @{winner}")
        # Повідомити учасників
        for username in participants:
            user_id = get_user_id(username)
            if user_id:
                await bot.send_message(user_id, f"🎉 Розіграш {raffle_id} завершено! Переможець: @{winner}")
    except:
        await msg.answer("❌ Використання: /closeraffle <raffle_id>")

# ---------------- ЗАПУСК ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
