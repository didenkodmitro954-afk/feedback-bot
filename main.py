import asyncio
import logging
import sqlite3
import time
import random

from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command

# ================= НАСТРОЙКИ =================
TOKEN = "8511337609:AAFNtvQWoD4rhyYugouVgsspw0FKorm-rDM"
OWNER_USERNAME = "userveesna"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ================= БАЗА =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    notified INTEGER DEFAULT 0
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS admins (
    username TEXT PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS tickets (
    user_id INTEGER PRIMARY KEY,
    admin_username TEXT,
    last_time INTEGER
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS giveaways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    end_time INTEGER,
    active INTEGER
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS giveaway_users (
    giveaway_id INTEGER,
    user_id INTEGER,
    UNIQUE(giveaway_id, user_id)
)""")

conn.commit()
cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (OWNER_USERNAME,))
conn.commit()

# ================= HELPERS =================
def is_admin(username):
    cur.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    return cur.fetchone() is not None

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

# ================= /start =================
@router.message(Command("start"))
async def start(msg: types.Message):
    cur.execute(
        "INSERT OR IGNORE INTO users VALUES (?,?,0)",
        (msg.from_user.id, msg.from_user.username)
    )
    conn.commit()

    await msg.answer(
        "👋 Вітаємо!\n\n"
        "✉️ Напишіть повідомлення — адміністрація відповість"
    )

# ================= /ahelp =================
@router.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return

    await msg.answer(
        "⚙️ Адмін-команди:\n"
        "/take @user\n"
        "/reply @user текст\n"
        "/closeticket @user\n"
        "/creategiveaway Назва | хвилини\n"
        "/delgiveaway ID\n"
        "/join ID\n"
        "/a текст\n"
        "/o текст\n"
        "/addadmin @user (GA)\n"
        "/deladmin @user (GA)"
    )

# ================= ТІКЕТИ =================
@router.message(Command("take"))
async def take(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        username = msg.text.split()[1].replace("@","")
        user_id = get_user_id(username)
        if not user_id:
            return await msg.answer("❌ Користувача не знайдено")

        ticket = get_ticket(user_id)
        if ticket:
            return await msg.answer("❌ Тікет уже взяли")

        take_ticket(user_id, msg.from_user.username)
        await bot.send_message(user_id, f"👮 Адміністратор @{msg.from_user.username} взяв ваш тікет")

        for admin in get_admins():
            if admin != msg.from_user.username:
                uid = get_user_id(admin)
                if uid:
                    await bot.send_message(uid, f"📌 @{msg.from_user.username} взяв тікет @{username}")

        await msg.answer("✅ Тікет взято")
    except:
        await msg.answer("❌ /take @username")

@router.message(Command("reply"))
async def reply(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        _, username, text = msg.text.split(" ", 2)
        username = username.replace("@","")
        user_id = get_user_id(username)

        ticket = get_ticket(user_id)
        if not ticket or ticket[0] != msg.from_user.username:
            return await msg.answer("❌ Спочатку /take")

        await bot.send_message(user_id, f"💬 Адмін:\n{text}")
        await msg.answer("✅ Надіслано")
    except:
        await msg.answer("❌ /reply @user текст")

@router.message(Command("closeticket"))
async def closeticket(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        username = msg.text.split()[1].replace("@","")
        user_id = get_user_id(username)
        close_ticket(user_id)
        await bot.send_message(user_id, "✅ Тікет закрито")
        await msg.answer("✅ Готово")
    except:
        await msg.answer("❌ /closeticket @user")

# ================= РОЗІГРАШІ =================
@router.message(Command("creategiveaway"))
async def creategiveaway(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        data = msg.text.replace("/creategiveaway","").strip()
        title, minutes = data.split("|")
        end_time = int(time.time()) + int(minutes.strip()) * 60
    except:
        return await msg.answer("❌ /creategiveaway Назва | хвилини")

    cur.execute(
        "INSERT INTO giveaways (title,end_time,active) VALUES (?,?,1)",
        (title.strip(), end_time)
    )
    gid = cur.lastrowid
    conn.commit()

    for admin in get_admins():
        uid = get_user_id(admin)
        if uid:
            await bot.send_message(uid, f"🎉 @{msg.from_user.username} створив розіграш #{gid}")

    await msg.answer(f"✅ Розіграш #{gid} створено")

@router.message(Command("join"))
async def join(msg: types.Message):
    try:
        gid = int(msg.text.split()[1])
    except:
        return await msg.answer("❌ /join ID")

    cur.execute("SELECT active FROM giveaways WHERE id=?", (gid,))
    row = cur.fetchone()
    if not row or row[0] == 0:
        return await msg.answer("❌ Розіграш неактивний")

    cur.execute(
        "INSERT OR IGNORE INTO giveaway_users VALUES (?,?)",
        (gid, msg.from_user.id)
    )
    conn.commit()

    await msg.answer("✅ Ви у розіграші")

async def giveaway_watcher():
    while True:
        now = int(time.time())
        cur.execute("SELECT id,title FROM giveaways WHERE active=1 AND end_time<=?", (now,))
        for gid,title in cur.fetchall():
            cur.execute("SELECT user_id FROM giveaway_users WHERE giveaway_id=?", (gid,))
            users = [u[0] for u in cur.fetchall()]
            if users:
                winner = random.choice(users)
                await bot.send_message(winner, f"🏆 Ви виграли: {title}")
            cur.execute("UPDATE giveaways SET active=0 WHERE id=?", (gid,))
            conn.commit()
        await asyncio.sleep(5)

# ================= АДМІН-ЧАТ =================
@router.message(Command("a"))
async def admin_chat(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    text = msg.text[3:].strip()
    for admin in get_admins():
        uid = get_user_id(admin)
        if uid:
            await bot.send_message(uid, f"💬 @{msg.from_user.username}:\n{text}")

# ================= ОГОЛОШЕННЯ =================
@router.message(Command("o"))
async def broadcast(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    text = msg.text[3:].strip()
    cur.execute("SELECT user_id FROM users")
    for uid in cur.fetchall():
        await bot.send_message(uid[0], f"📢 Оголошення:\n{text}")
    await msg.answer("✅ Надіслано")

# ================= GA =================
@router.message(Command("addadmin"))
async def addadmin(msg: types.Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    username = msg.text.split()[1].replace("@","")
    cur.execute("INSERT OR IGNORE INTO admins VALUES (?)",(username,))
    conn.commit()
    await msg.answer("✅ Адмін доданий")

@router.message(Command("deladmin"))
async def deladmin(msg: types.Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    username = msg.text.split()[1].replace("@","")
    if username == OWNER_USERNAME:
        return
    cur.execute("DELETE FROM admins WHERE username=?", (username,))
    conn.commit()
    await msg.answer("✅ Адмін видалений")

# ================= USER MSG =================
@router.message()
async def user_msg(msg: types.Message):
    if is_admin(msg.from_user.username):
        return
    await msg.answer("✅ Повідомлення надіслано")
    ticket = get_ticket(msg.from_user.id)
    for admin in get_admins():
        if ticket and admin != ticket[0]:
            continue
        uid = get_user_id(admin)
        if uid:
            await bot.send_message(uid, f"📩 @{msg.from_user.username}:\n{msg.text}")

# ================= RUN =================
async def main():
    asyncio.create_task(giveaway_watcher())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
