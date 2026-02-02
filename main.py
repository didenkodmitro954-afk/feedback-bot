import logging
from aiogram import Bot, Dispatcher, executor, types
import sqlite3

# ---------------- Налаштування ----------------
TOKEN = "8468725441:AAFTU2RJfOH3Eo__nJtEw1NqUbj5Eu3cTUE"  # твій токен сюди
OWNER_USERNAME = "userveesna"  # головний адмін

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

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
conn.commit()

# Ініціалізація головного адміна
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

# ---------------- Команди користувачів ----------------
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)
    await msg.answer(
        "🎉 ВІТАЄМО У НАШОМУ БОТІ! 🎉\n\n"
        "👋 Привіт, @{username}!\n\n"
        "Ви можете ознайомитися із нашим прайс листом: https://t.me/praiceabn\n"
        "Головний канал: https://t.me/reklamaabn\n\n"
        "Ти можеш приєднатися до розіграшів через /join<id>\n"
        "Переглянути розіграші: /giveaways\n"
        "Напиши повідомлення, і адмін відповість.".format(username=msg.from_user.username)
    )

    # повідомлення адмінам про нового користувача лише раз
    new_users = get_new_users()
    for user_id, username in new_users:
        for admin_id in get_users():
            if admin_id != user_id:
                try:
                    await bot.send_message(
                        admin_id,
                        f"🆕 Новий користувач зареєстрований:\n"
                        f"ID: {user_id}\nUsername: @{username}"
                    )
                except:
                    pass
        mark_notified(user_id)

@dp.message_handler(commands=["giveaways"])
async def giveaways(msg: types.Message):
    gvs = get_active_giveaways()
    if not gvs:
        await msg.answer("❌ Немає активних розіграшів.")
        return
    text = "🎁 Активні розіграші:\n"
    for g in gvs:
        text += f"\nID {g[0]} — {g[1]} /join{g[0]}"
    await msg.answer(text)

@dp.message_handler(lambda m: m.text.startswith("/join"))
async def join(msg: types.Message):
    try:
        gid = int(msg.text.replace("/join", ""))
        join_giveaway(gid, msg.from_user.id)
        await msg.answer("✅ Ви приєдналися до розіграшу!")
    except:
        await msg.answer("❌ Невірна команда. Використання: /join<id>")

# ---------------- Команди адмінів ----------------
@dp.message_handler(commands=["ahelp"])
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    text = (
        "⚙️ Команди адміністратора:\n"
        "/ahelp — список команд\n"
        "/addadmin <username> — додати адміна\n"
        "/reply <user_id> <текст> — відповісти користувачу\n"
        "/creategiveaway Назва | дні — створити розіграш\n"
        "/giveaways — активні розіграші"
    )
    await msg.answer(text)

@dp.message_handler(commands=["addadmin"])
async def addadmin(msg: types.Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    try:
        username = msg.text.split()[1].replace("@","")
        add_admin(username)
        await msg.answer(f"✅ @{username} додано як адмін")
    except:
        await msg.answer("❌ Використання: /addadmin <username>")

@dp.message_handler(commands=["reply"])
async def reply(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        _, user_id, text = msg.text.split(" ",2)
        await bot.send_message(int(user_id), f"💬 Відповідь адміна:\n{text}")
        await msg.answer("✅ Відправлено")
    except:
        await msg.answer("❌ Використання: /reply <user_id> <текст>")

@dp.message_handler(commands=["creategiveaway"])
async def creategiveaway(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        data = msg.text.replace("/creategiveaway","").strip()
        title, days = data.split("|")
        gid = create_giveaway(title.strip(), int(days.strip()))
        # повідомлення всім користувачам
        for user_id in get_users():
            try:
                await bot.send_message(
                    user_id,
                    f"🎉 НОВИЙ РОЗІГРАШ!\n"
                    f"{title.strip()}\n"
                    f"⏳ Тривалість: {days.strip()} днів\n"
                    f"👉 /join{gid}"
                )
            except:
                pass
        await msg.answer(f"✅ Розіграш створено (ID {gid})")
    except:
        await msg.answer("❌ Використання: /creategiveaway Назва | дні")

# ---------------- Пересилання повідомлень користувачів адмінам ----------------
@dp.message_handler()
async def forward_to_admins(msg: types.Message):
    for admin_id in get_users():
        if is_admin(msg.from_user.username) or admin_id != msg.from_user.id:
            try:
                await bot.send_message(
                    admin_id,
                    f"📩 Повідомлення від @{msg.from_user.username} (ID {msg.from_user.id}):\n{msg.text}"
                )
            except:
                pass

# ---------------- Запуск ----------------
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
