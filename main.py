import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

BOT_TOKEN = "8468725441:AAFTU2RJfOH3Eo__nJtEw1NqUbj5Eu3cTUE"
OWNER_USERNAME = "userveesna"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ---------------- ДАНІ ----------------
users = {}        # username -> user_id
admins = set()    # user_id
admins_usernames = set()  # username для перевірки
admins_usernames.add(OWNER_USERNAME)
giveaways = {}    # id: {title, end_time, participants}
tickets = {}      # username -> admin_username
tickets_taken = {} # username -> bool
registrations = set()

giveaway_counter = 1

# ---------------- ФУНКЦІЇ ----------------
def is_admin(user_id):
    return user_id in admins

async def notify_admins(text):
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, text)
        except:
            pass

# ---------------- КОМАНДИ ----------------
@dp.message(Command("start"))
async def start(msg: Message):
    username = msg.from_user.username or f"id{msg.from_user.id}"
    users[username] = msg.from_user.id

    await msg.answer(
        f"🎉 Привіт @{username}!\n\n"
        "✅ Ви успішно звернулися до підтримки.\n"
        "✉️ Напишіть повідомлення — адміністратор відповість.\n\n"
        "💰 Ознайомитися з прайс листом: https://t.me/praiceabn\n"
        "📣 Основний канал: https://t.me/reklamaabn"
    )

    if username not in registrations:
        registrations.add(username)
        await notify_admins(f"🆕 Новий користувач зареєстрований!\n👤 @{username}")

# ---------------- ЗВЕРНЕННЯ ----------------
@dp.message(F.text & ~F.text.startswith("/"))
async def forward_message(msg: Message):
    username = msg.from_user.username or f"id{msg.from_user.id}"
    users[username] = msg.from_user.id

    # Якщо користувач не закріплений за адміном
    if username not in tickets:
        await notify_admins(f"📨 Нове звернення\n👤 @{username}\n💬 {msg.text}\n👉 /take @{username}")
    else:
        admin_username = tickets[username]
        await bot.send_message(users[admin_username], f"📩 Від @{username}:\n{msg.text}")

    await msg.answer("✅ Повідомлення успішно надіслано.")

# ---------------- /addadmin ----------------
@dp.message(Command("addadmin"))
async def addadmin(msg: Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    try:
        username = msg.text.split()[1].replace("@","")
        if username not in users:
            return await msg.answer("❌ Користувач ще не писав боту")
        admins.add(users[username])
        admins_usernames.add(username)
        await msg.answer(f"✅ @{username} додано як адмін")
    except:
        await msg.answer("❌ /addadmin @username")

# ---------------- /deladmin ----------------
@dp.message(Command("deladmin"))
async def deladmin(msg: Message):
    if msg.from_user.username != OWNER_USERNAME:
        return
    try:
        username = msg.text.split()[1].replace("@","")
        if username == OWNER_USERNAME:
            return await msg.answer("❌ Неможливо видалити головного адміна")
        admins.discard(users.get(username,0))
        admins_usernames.discard(username)
        await msg.answer(f"✅ @{username} видалено з адмінів")
    except:
        await msg.answer("❌ /deladmin @username")

# ---------------- /reply ----------------
@dp.message(Command("reply"))
async def reply(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        parts = msg.text.split(" ",2)
        username = parts[1].replace("@","")
        text = parts[2]
        if username not in users:
            return await msg.answer("❌ Користувач не знайдений")
        await bot.send_message(users[username], f"💬 Відповідь адміна:\n{text}")
        await msg.answer("✅ Відправлено")
    except:
        await msg.answer("❌ /reply @username текст")

# ---------------- /take ----------------
@dp.message(Command("take"))
async def take_ticket(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        username = msg.text.split()[1].replace("@","")
        if username not in users:
            return await msg.answer("❌ Користувач не знайдений")
        if username in tickets:
            return await msg.answer("❌ Тікет вже закріплений за іншим адміном")
        tickets[username] = msg.from_user.username
        tickets_taken[username] = False
        if not tickets_taken[username]:
            await notify_admins(f"📌 Тікет @{username} взяв @{msg.from_user.username}")
            tickets_taken[username] = True
        await msg.answer(f"✅ Ви взяли тікет @{username}")
    except:
        await msg.answer("❌ /take @username")

# ---------------- /close ----------------
@dp.message(Command("close"))
async def close_ticket(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        username = msg.text.split()[1].replace("@","")
        if username not in tickets:
            return await msg.answer("❌ Тікет не знайдено")
        tickets.pop(username)
        tickets_taken.pop(username,None)
        await notify_admins(f"❌ Тікет @{username} закрито @{msg.from_user.username}")
        await msg.answer(f"✅ Тікет @{username} закрито")
    except:
        await msg.answer("❌ /close @username")

# ---------------- /ahelp ----------------
@dp.message(Command("ahelp"))
async def ahelp(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    text = (
        "⚙️ Команди адміністратора:\n"
        "/ahelp — список команд\n"
        "/addadmin @username — додати адміна\n"
        "/deladmin @username — видалити адміна\n"
        "/reply @username текст — відповісти користувачу\n"
        "/take @username — взяти тікет\n"
        "/close @username — закрити тікет\n"
        "/creategiveaway Назва | дні — створити розіграш\n"
        "/join<ID> — приєднатися до розіграшу"
    )
    await msg.answer(text)

# ---------------- РОЗІГРАШІ ----------------
@dp.message(Command("creategiveaway"))
async def creategiveaway(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    try:
        global giveaway_counter
        data = msg.text.replace("/creategiveaway","").strip()
        title, days = data.split("|")
        end_time = datetime.now() + timedelta(days=int(days.strip()))
        giveaways[giveaway_counter] = {"title": title.strip(), "end_time": end_time, "participants": set()}
        gid = giveaway_counter
        giveaway_counter +=1
        for uname, uid in users.items():
            await bot.send_message(uid,f"🎉 НОВИЙ РОЗІГРАШ!\n{title.strip()}\n⏳ {days.strip()} днів\n👉 /join{gid}")
        await msg.answer(f"✅ Розіграш створено (ID {gid})")
    except:
        await msg.answer("❌ /creategiveaway Назва | дні")

@dp.message(lambda m: m.text.startswith("/join"))
async def join_giveaway(msg: Message):
    try:
        gid = int(msg.text.replace("/join",""))
        if gid not in giveaways:
            return await msg.answer("❌ Розіграш не знайдено")
        giveaways[gid]["participants"].add(msg.from_user.username)
        await msg.answer("✅ Ви приєдналися до розіграшу!")
    except:
        await msg.answer("❌ /join<ID>")

# ---------------- Автоматичне завершення розіграшів ----------------
async def check_giveaways():
    while True:
        now = datetime.now()
        for gid, gv in list(giveaways.items()):
            if gv["end_time"] <= now and gv["participants"]:
                winner = random.choice(list(gv["participants"]))
                text = f"🏆 Розіграш '{gv['title']}' завершено!\nПереможець: @{winner}"
                for uname, uid in users.items():
                    await bot.send_message(uid,text)
                giveaways.pop(gid)
        await asyncio.sleep(60)

# ---------------- Запуск ----------------
async def main():
    admins.add(users.get(OWNER_USERNAME,0))
    await asyncio.gather(dp.start_polling(bot), check_giveaways())

if __name__ == "__main__":
    asyncio.run(main())
