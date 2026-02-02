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
CREATE TABLE IF NOT EXISTS tickets (
    user_id INTEGER PRIMARY KEY,
    admin_username TEXT,
    notified INTEGER DEFAULT 0,
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

# Додаємо головного адміна
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
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (uid, username))
    conn.commit()

def get_user_id(username):
    cur.execute("SELECT user_id FROM users WHERE username=?", (username,))
    r = cur.fetchone()
    return r[0] if r else None

# ---------- Тікети ----------
def take_ticket(user_id, admin):
    cur.execute("INSERT OR REPLACE INTO tickets VALUES (?,?,?,?)", (user_id, admin, 0, int(time.time())))
    conn.commit()

def get_ticket(user_id):
    cur.execute("SELECT admin_username, notified, last_time FROM tickets WHERE user_id=?", (user_id,))
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
    cur.execute("INSERT INTO giveaways (title, end_time, active) VALUES (?,?,1)", (title, end_time))
    conn.commit()
    return cur.lastrowid, end_time

def close_giveaway(gid):
    cur.execute("UPDATE giveaways SET active=0 WHERE id=?", (gid,))
    conn.commit()

def get_active_giveaways():
    cur.execute("SELECT id, title FROM giveaways WHERE active=1")
    return cur.fetchall()

def join_giveaway(gid, user_id):
    cur.execute("INSERT OR IGNORE INTO giveaway_users VALUES (?,?)", (gid, user_id))
    conn.commit()

# ================= /start =================
@dp.message(Command("start"))
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username)
    await msg.answer(
        "👋 Ласкаво просимо!\n\n"
        "✅ Ви успішно зареєстровані\n"
        "✉️ Напишіть повідомлення — адміністрація відповість\n\n"
        "💰 Прайс-лист:\nhttps://t.me/praiceabn\n"
        "📣 Основний канал:\nhttps://t.me/reklamaabn"
    )

    cur.execute("SELECT notified FROM users WHERE user_id=?", (msg.from_user.id,))
    if cur.fetchone()[0] == 0:
        for admin in get_admins():
            uid = get_user_id(admin)
            if uid:
                await bot.send_message(uid,
                    f"🆕 Новий користувач зареєстрований:\n"
                    f"👤 @{msg.from_user.username}\n"
                    f"🆔 {msg.from_user.id}"
                )
        cur.execute("UPDATE users SET notified=1 WHERE user_id=?", (msg.from_user.id,))
        conn.commit()

# ================= /ahelp =================
@dp.message(Command("ahelp"))
async def ahelp(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    await msg.answer(
        "⚙️ Адмін-команди:\n"
        "/reply @user текст — відповісти на тікет\n"
        "/closeticket @user — закрити тікет\n"
        "/take @user — взяти тікет\n"
        "/creategiveaway Назва | дні — створити розіграш\n"
        "/delgiveaway ID — закрити розіграш\n"
        "/giveaways — список активних розіграшів\n"
        "/a текст — повідомлення всім адмінам\n"
        "/o текст — оголошення всім користувачам\n"
    )

# ================= /reply =================
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
        if ticket and ticket[0] and ticket[0] != msg.from_user.username:
            await msg.answer("❌ Тікет вже взяв інший адмін")
            return
        take_ticket(user_id, msg.from_user.username)
        await bot.send_message(user_id, f"👮 Адміністратор відповів:\n{text}")
        if ticket and ticket[1] == 0:
            for admin in get_admins():
                if admin != msg.from_user.username:
                    uid = get_user_id(admin)
                    if uid:
                        await bot.send_message(uid, f"📌 Адмін @{msg.from_user.username} взяв тікет @{username}")
            mark_ticket_notified(user_id)
        await msg.answer("✅ Відповідь надіслано")
    except:
        await msg.answer("❌ /reply @username текст")

# ================= /closeticket =================
@dp.message(Command("closeticket"))
async def closeticket(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        _, username = msg.text.split()
        username = username.replace("@", "")
        user_id = get_user_id(username)
        close_ticket(user_id)
        await bot.send_message(user_id, "✅ Звернення закрито. Можете написати знову у будь-який момент.")
        await msg.answer("✅ Тікет закрито")
    except:
        await msg.answer("❌ /closeticket @username")

# ================= /take =================
@dp.message(Command("take"))
async def take(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        _, username = msg.text.split()
        username = username.replace("@", "")
        user_id = get_user_id(username)
        take_ticket(user_id, msg.from_user.username)
        await msg.answer(f"✅ Ви взяли тікет @{username}")
        ticket = get_ticket(user_id)
        if ticket and ticket[1] == 0:
            for admin in get_admins():
                if admin != msg.from_user.username:
                    uid = get_user_id(admin)
                    if uid:
                        await bot.send_message(uid, f"📌 Адмін @{msg.from_user.username} взяв тікет @{username}")
            mark_ticket_notified(user_id)
    except:
        await msg.answer("❌ /take @username")

# ================= /creategiveaway =================
@dp.message(Command("creategiveaway"))
async def creategv(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        data = msg.text.replace("/creategiveaway","").strip()
        title, days = data.split("|")
        gid, end_time = create_giveaway(title.strip(), int(days.strip()))
        for u in get_admins():
            uid = get_user_id(u)
            if uid:
                await bot.send_message(uid, f"🎉 Новий розіграш!\n{title.strip()}\n👉 /join{gid}")
        asyncio.create_task(finish_giveaway(gid, end_time))
        await msg.answer(f"✅ Розіграш створено (ID {gid})")
    except:
        await msg.answer("❌ /creategiveaway Назва | дні")

# ================= /delgiveaway =================
@dp.message(Command("delgiveaway"))
async def delgv(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    try:
        gid = int(msg.text.split()[1])
        close_giveaway(gid)
        await msg.answer("✅ Розіграш закрито")
    except:
        await msg.answer("❌ /delgiveaway ID")

# ================= /giveaways =================
@dp.message(Command("giveaways"))
async def giveaways(msg: types.Message):
    gvs = get_active_giveaways()
    if not gvs:
        await msg.answer("❌ Немає активних розіграшів")
        return
    text = "🎁 Активні розіграші:\n"
    for g in gvs:
        text += f"ID {g[0]} — {g[1]} /join{g[0]}\n"
    await msg.answer(text)

# ================= /join =================
@dp.message(lambda m: m.text.startswith("/join"))
async def join(msg: types.Message):
    try:
        gid = int(msg.text.replace("/join",""))
        join_giveaway(gid, msg.from_user.id)
        await msg.answer("✅ Ви приєдналися до розіграшу!")
    except:
        await msg.answer("❌ /joinID")

# ================= Завершення розіграшу =================
async def finish_giveaway(gid, end_time):
    await asyncio.sleep(max(0, end_time - time.time()))
    cur.execute("SELECT user_id FROM giveaway_users WHERE giveaway_id=?", (gid,))
    users = cur.fetchall()
    if not users:
        return
    winner = random.choice(users)[0]
    close_giveaway(gid)
    for u in get_admins():
        uid = get_user_id(u)
        if uid:
            await bot.send_message(uid, f"🏆 Переможець розіграшу ID {gid}:\n🆔 {winner}")

# ================= /a — повідомлення всім адмінам =================
@dp.message(Command("a"))
async def admin_msg(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    text = msg.text.replace("/a","").strip()
    for u in get_admins():
        if u != msg.from_user.username:
            uid = get_user_id(u)
            if uid:
                await bot.send_message(uid, f"👤 @{msg.from_user.username} написав:\n{text}")
    await msg.answer("✅ Повідомлення відправлено всім адмінам")

# ================= /o — оголошення всім користувачам =================
@dp.message(Command("o"))
async def announcement(msg: types.Message):
    if not is_admin(msg.from_user.username):
        return
    text = msg.text.replace("/o","").strip()
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    for u in users:
        try:
            await bot.send_message(u[0], f"📢 Оголошення:\n{text}")
        except:
            pass
    await msg.answer("✅ Оголошення відправлено всім користувачам")

# ================= Повідомлення від користувача =================
@dp.message()
async def user_msg(msg: types.Message):
    if is_admin(msg.from_user.username):
        return
    await msg.answer("✅ Повідомлення надіслано адміністрації")
    ticket = get_ticket(msg.from_user.id)
    if ticket and time.time() - ticket[2] > 1800:
        close_ticket(msg.from_user.id)
        ticket = None
    for admin in get_admins():
        if ticket and admin != ticket[0]:
            continue
        uid = get_user_id(admin)
        if uid:
            await bot.send_message(uid, f"📩 @{msg.from_user.username}:\n{msg.text}")

# ================= ЗАПУСК =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
