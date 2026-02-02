import asyncio
import logging
import sqlite3
import time
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# ================= НАСТРОЙКИ =================
TOKEN = "8468725441:AAFTU2RJfOH3Eo__nJtEw1NqUbj5Eu3cTUE"
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

# ---------- Розіграші ----------
def create_giveaway(title, days):
    end_time = int(time.time()) + days * 86400
    cur.execute(
        "INSERT INTO giveaways (title, end_time, active) VALUES (?,?,1)",
        (title, end_time)
    )
    conn.commit()
    return cur.lastrowid, end_time

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

# ================= /start =================
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)

    await msg.answer(
        "👋 Вітаємо!\n\n"
        "✅ Ви успішно зареєстровані\n\n"
        "✉️ Напишіть повідомлення — адміністрація відповість\n\n"
        "💰 Прайс-лист:\nhttps://t.me/praiceabn\n"
        "📣 Основний канал:\nhttps://t.me/reklamaabn"
    )

    cur.execute("SELECT notified FROM users WHERE user_id=?", (msg.from_user.id,))
    if cur.fetchone()[0] == 0:
        for admin in get_admins():
            uid = get_user_id(admin)
            if uid:
                await bot.send_message(
                    uid,
                    f"🆕 Новий користувач:\n👤 @{msg.from_user.username}\n🆔 {msg.from_user.id}"
                )
        cur.execute(
            "UPDATE users SET notified=1 WHERE user_id=?",
            (msg.from_user.id,)
        )
        conn.commit()

# ================= /ahelp =================
@dp.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return

    await msg.answer(
        "⚙️ Адмін-команди:\n\n"
        "/reply @user текст — відповісти у тікеті\n"
        "/take @user — взяти тікет\n"
        "/closeticket @user — закрити тікет\n"
        "/creategiveaway Назва | дні — створити розіграш\n"
        "/delgiveaway ID — закрити розіграш\n"
        "/giveaways — активні розіграші\n"
        "/addadmin @user — видати адмінку (тільки головний)"
    )

# ================= /addadmin =================
@dp.message(Command("addadmin"))
async def addadmin(msg: types.Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    try:
        username = msg.text.split()[1].replace("@","")
        uid = get_user_id(username)
        if not uid:
            return await msg.answer("❌ Користувач ще не писав боту")
        cur.execute("INSERT OR IGNORE INTO admins VALUES (?)", (username,))
        conn.commit()
        await msg.answer(f"✅ @{username} отримав адмінку")
    except:
        await msg.answer("❌ /addadmin @username")

# ================= /take =================
@dp.message(Command("take"))
async def take(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        username = msg.text.split()[1].replace("@","")
        uid = get_user_id(username)
        if not uid:
            return await msg.answer("❌ Користувач не знайдений")
        ticket = get_ticket(uid)
        if ticket and ticket[0] != msg.from_user.username:
            return await msg.answer("❌ Тікет вже взяв інший адмін")
        take_ticket(uid, msg.from_user.username)
        if ticket is None or ticket[1]==0:
            # сповіщення про взяття тільки раз
            for admin in get_admins():
                aid = get_user_id(admin)
                if aid:
                    await bot.send_message(aid,f"📌 Тікет @{username} взяв @{msg.from_user.username}")
            mark_ticket_notified(uid)
        await msg.answer(f"✅ Ви взяли тікет @{username}")
    except:
        await msg.answer("❌ /take @username")

# ================= /reply =================
@dp.message(Command("reply"))
async def reply(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        _, username, text = msg.text.split(" ", 2)
        username = username.replace("@","")
        uid = get_user_id(username)
        if not uid:
            return await msg.answer("❌ Користувач не знайдений")
        ticket = get_ticket(uid)
        if ticket and ticket[0] != msg.from_user.username:
            return await msg.answer("❌ Тікет вже взяв інший адмін")
        take_ticket(uid, msg.from_user.username)
        await bot.send_message(uid,f"💬 Відповідь адміна:\n{text}")
        await msg.answer("✅ Відправлено")
    except:
        await msg.answer("❌ /reply @username текст")

# ================= /closeticket =================
@dp.message(Command("closeticket"))
async def closeticket(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        username = msg.text.split()[1].replace("@","")
        uid = get_user_id(username)
        close_ticket(uid)
        await bot.send_message(uid,"✅ Ваш тікет закрито. Можете писати знову")
        await msg.answer("✅ Тікет закрито")
    except:
        await msg.answer("❌ /closeticket @username")

# ================= /creategiveaway =================
@dp.message(Command("creategiveaway"))
async def creategv(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        data = msg.text.replace("/creategiveaway","").strip()
        title, days = data.split("|")
        gid, end_time = create_giveaway(title.strip(), int(days.strip()))
        for uid, uname in [(r[0], r[1]) for r in cur.execute("SELECT user_id, username FROM users")]:
            await bot.send_message(uid,f"🎉 Новий розіграш!\n{title.strip()}\n⏳ {days.strip()} днів\n👉 /join{gid}")
        asyncio.create_task(finish_giveaway(gid,end_time))
        await msg.answer(f"✅ Розіграш створено (ID {gid})")
    except:
        await msg.answer("❌ /creategiveaway Назва | дні")

async def finish_giveaway(gid, end_time):
    await asyncio.sleep(max(0,end_time - time.time()))
    cur.execute("SELECT user_id FROM giveaway_users WHERE giveaway_id=?", (gid,))
    participants = cur.fetchall()
    if not participants:
        close_giveaway(gid)
        return
    winner = random.choice(participants)[0]
    close_giveaway(gid)
    for uid, uname in [(r[0], r[1]) for r in cur.execute("SELECT user_id, username FROM users")]:
        await bot.send_message(uid,f"🏆 Розіграш завершено! Переможець: 🆔 {winner}")

# ================= /join =================
@dp.message(lambda m: m.text.startswith("/join"))
async def join_giveaway_cmd(msg: types.Message):
    try:
        gid = int(msg.text.replace("/join",""))
        join_giveaway(gid,msg.from_user.id)
        await msg.answer("✅ Ви приєдналися до розіграшу!")
    except:
        await msg.answer("❌ /join<ID>")

# ================= Повідомлення користувача =================
@dp.message()
async def user_msg(msg: types.Message):
    if is_admin(msg.from_user.username):
        return
    await msg.answer("✅ Повідомлення надіслано адміністрації")
    uid = msg.from_user.id
    ticket = get_ticket(uid)
    if ticket and time.time()-ticket[2]>1800:  # 30 хв
        close_ticket(uid)
        ticket = None
    for admin in get_admins():
        if ticket and admin != ticket[0]:
            continue
        aid = get_user_id(admin)
        if aid:
            await bot.send_message(aid,f"📩 @{msg.from_user.username}:\n{msg.text}")

# ================= Запуск =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
