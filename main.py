import asyncio
import logging
import sqlite3
import time
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================= НАСТРОЙКИ =================
TOKEN = "8511337609:AAFNtvQWoD4rhyYugouVgsspw0FKorm-rDM"
OWNER_USERNAME = "userveesna"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
    notified INTEGER,
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

# ================= ФУНКЦІЇ =================
def is_admin(username):
    cur.execute("SELECT 1 FROM admins WHERE username=?", (username,))
    return cur.fetchone() is not None

def get_admins():
    cur.execute("SELECT username FROM admins")
    return [x[0] for x in cur.fetchall()]

def add_user(uid, username):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?,?,0)", (uid, username))
    conn.commit()

def get_user_id(username):
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    r = cur.fetchone()
    return r[0] if r else None

# ================= РОЗІГРАШІ =================
def create_giveaway(title, days):
    end_time = int(time.time()) + days * 86400
    cur.execute(
        "INSERT INTO giveaways (title, end_time, active) VALUES (?,?,1)",
        (title, end_time)
    )
    conn.commit()
    return cur.lastrowid, end_time

def get_active_giveaways():
    cur.execute("SELECT id, title, end_time FROM giveaways WHERE active=1")
    return cur.fetchall()

def join_giveaway(gid, user_id):
    cur.execute("INSERT OR IGNORE INTO giveaway_users VALUES (?,?)", (gid, user_id))
    conn.commit()

def close_giveaway(gid):
    cur.execute("UPDATE giveaways SET active=0 WHERE id=?", (gid,))
    conn.commit()

async def finish_giveaway(gid, end_time):
    await asyncio.sleep(max(0, end_time - time.time()))
    cur.execute("SELECT user_id FROM giveaway_users WHERE giveaway_id=?", (gid,))
    users = cur.fetchall()
    close_giveaway(gid)

    if not users:
        return

    winner = random.choice(users)[0]
    for admin in get_admins():
        uid = get_user_id(admin)
        if uid:
            await bot.send_message(uid, f"🏆 Розіграш ID {gid}\nПереможець: {winner}")

# ================= /creategiveaway =================
@dp.message(Command("creategiveaway"))
async def create_gv(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        data = msg.text.replace("/creategiveaway", "").strip()
        title, days = data.split("|")
        gid, end_time = create_giveaway(title.strip(), int(days.strip()))

        for admin in get_admins():
            uid = get_user_id(admin)
            if uid:
                await bot.send_message(
                    uid,
                    f"🎉 @{msg.from_user.username} створив розіграш\n"
                    f"📌 {title.strip()}\n"
                    f"👉 /join{gid}"
                )

        asyncio.create_task(finish_giveaway(gid, end_time))
        await msg.answer(f"✅ Розіграш створено (ID {gid})")
    except:
        await msg.answer("❌ /creategiveaway Назва | дні")

# ================= /giveaways =================
@dp.message(Command("giveaways"))
async def giveaways(msg: types.Message):
    gvs = get_active_giveaways()
    if not gvs:
        await msg.answer("❌ Активних розіграшів немає")
        return

    text = "🎁 Активні розіграші:\n\n"
    for g in gvs:
        text += f"ID {g[0]} — {g[1]}\n👉 /join{g[0]}\n\n"
    await msg.answer(text)

# ================= /joinID =================
@dp.message(lambda m: m.text.startswith("/join"))
async def join(msg: types.Message):
    try:
        gid = int(msg.text.replace("/join", ""))
        join_giveaway(gid, msg.from_user.id)
        await msg.answer("✅ Ви успішно приєдналися до розіграшу!")
    except:
        await msg.answer("❌ Використання: /joinID")

# ================= АВТО-ВІДНОВЛЕННЯ РОЗІГРАШІВ =================
async def restore_giveaways():
    cur.execute("SELECT id, end_time FROM giveaways WHERE active=1")
    for gid, end_time in cur.fetchall():
        asyncio.create_task(finish_giveaway(gid, end_time))

# ================= ЗАПУСК =================
async def main():
    await restore_giveaways()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
