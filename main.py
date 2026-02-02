import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import sqlite3
from datetime import datetime

# ---------------- Налаштування ----------------
TOKEN = "8468725441:AAFTU2RJfOH3Eo__nJtEw1NqUbj5Eu3cTUE"
OWNER_ID = 1540349061  # твій Telegram ID

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
    admin_id INTEGER PRIMARY KEY
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

# Додаємо головного адміна
cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (OWNER_ID,))
conn.commit()

# ---------------- Функції ----------------
def add_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (user_id, username))
    conn.commit()

def mark_notified(user_id):
    cur.execute("UPDATE users SET notified=1 WHERE user_id=?", (user_id,))
    conn.commit()

def was_notified(user_id):
    cur.execute("SELECT notified FROM users WHERE user_id=?", (user_id,))
    res = cur.fetchone()
    return res[0] == 1 if res else False

def get_users():
    cur.execute("SELECT user_id FROM users")
    return [x[0] for x in cur.fetchall()]

def add_admin(admin_id):
    cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (admin_id,))
    conn.commit()

def del_admin(admin_id):
    cur.execute("DELETE FROM admins WHERE admin_id=?", (admin_id,))
    conn.commit()

def is_admin(user_id):
    cur.execute("SELECT 1 FROM admins WHERE admin_id=?", (user_id,))
    return cur.fetchone() is not None

def create_giveaway(title, days):
    cur.execute("INSERT INTO giveaways (title, days, active) VALUES (?,?,1)", (title, days))
    conn.commit()
    return cur.lastrowid

def get_active_giveaways():
    cur.execute("SELECT id, title FROM giveaways WHERE active=1")
    return cur.fetchall()

def join_giveaway(gid, user_id):
    cur.execute("INSERT OR IGNORE INTO giveaway_users VALUES (?,?)", (gid, user_id))
    conn.commit()

# ---------------- Команди користувачів ----------------
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)

    welcome_text = (
        f"🎉🎊 Ласкаво просимо, @{msg.from_user.username}! 🎊🎉\n\n"
        "🌟 Ознайомитися із нашим прайс листом: https://t.me/praiceabn\n"
        "📣 Основний канал: https://t.me/reklamaabn\n\n"
        "🎁 Розіграші: /giveaways\n"
        "💬 Надішліть повідомлення адміну, і він відповість."
    )
    await msg.answer(welcome_text)

    # Повідомлення адміну лише один раз
    if not was_notified(msg.from_user.id):
        try:
            await bot.send_message(
                OWNER_ID,
                f"🆕 Новий користувач зареєстрований!\n"
                f"👤 Username: @{msg.from_user.username}\n"
                f"🆔 ID: {msg.from_user.id}\n"
                f"⏰ Зареєстрований: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
        except: pass
        mark_notified(msg.from_user.id)

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
        gid = int(msg.text.replace("/join",""))
        join_giveaway(gid, msg.from_user.id)
        await msg.answer("✅ Ви приєдналися до розіграшу!")
    except:
        await msg.answer("❌ Невірна команда. Використання: /join<ID>")

# ---------------- Команди головного адміна ----------------
@dp.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if msg.from_user.id != OWNER_ID:
        return
    text = (
        "⚙️ Команди адміністратора:\n"
        "/ahelp — список команд\n"
        "/addadmin <ID> — додати адміна\n"
        "/deladmin <ID> — видалити адміна\n"
        "/reply <ID> текст — відповісти користувачу\n"
        "/creategiveaway Назва | дні — створити розіграш\n"
        "/giveaways — активні розіграші"
    )
    await msg.answer(text)

@dp.message(Command("addadmin"))
async def addadmin(msg: types.Message):
    if msg.from_user.id != OWNER_ID:
        return
    try:
        admin_id = int(msg.text.split()[1])
        add_admin(admin_id)
        await msg.answer(f"✅ Admin {admin_id} додано")
    except:
        await msg.answer("❌ Використання: /addadmin <ID>")

@dp.message(Command("deladmin"))
async def deladmin(msg: types.Message):
    if msg.from_user.id != OWNER_ID:
        return
    try:
        admin_id = int(msg.text.split()[1])
        if admin_id == OWNER_ID:
            await msg.answer("❌ Неможливо видалити головного адміна")
            return
        del_admin(admin_id)
        await msg.answer(f"✅ Admin {admin_id} видалено")
    except:
        await msg.answer("❌ Використання: /deladmin <ID>")

@dp.message(Command("reply"))
async def reply(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        parts = msg.text.split(" ", 2)
        user_id = int(parts[1])
        text = parts[2]
        await bot.send_message(user_id, f"💬 Відповідь адміна:\n{text}")
        await msg.answer("✅ Відправлено")
    except:
        await msg.answer("❌ Використання: /reply <ID> текст")

@dp.message(Command("creategiveaway"))
async def creategiveaway(msg: types.Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        data = msg.text.replace("/creategiveaway","").strip()
        title, days = data.split("|")
        gid = create_giveaway(title.strip(), int(days.strip()))
        for user_id in get_users():
            try:
                await bot.send_message(user_id, f"🎉 НОВИЙ РОЗІГРАШ!\n{title.strip()}\n⏳ Тривалість: {days.strip()} днів\n👉 /join{gid}")
            except:
                pass
        await msg.answer(f"✅ Розіграш створено (ID {gid})")
    except:
        await msg.answer("❌ Використання: /creategiveaway Назва | дні")

# ---------------- Зворотній зв'язок ----------------
@dp.message()
async def forward_to_admin(msg: types.Message):
    if is_admin(msg.from_user.id):
        return
    # Користувачу повідомлення про успішну відправку
    await msg.answer("✅ Ваше повідомлення успішно надіслано. Очікуйте відповіді адміністратора.")
    try:
        await bot.send_message(
            OWNER_ID,
            f"📩 Повідомлення від @{msg.from_user.username} (ID {msg.from_user.id}):\n{msg.text}"
        )
    except:
        pass

# ---------------- Запуск ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
