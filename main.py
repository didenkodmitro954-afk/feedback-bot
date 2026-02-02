import asyncio
import time
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from database import *

# ----------------- Налаштування -----------------
TOKEN = "ТУТ_ВСТАВ_СВІЙ_ТОКЕН"  # <-- твій токен
MAIN_ADMIN_USERNAME = "userveesna"  # твій username без @

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ----------------- Ініціалізація головного адміна -----------------
add_admin(MAIN_ADMIN_USERNAME)

# ----------------- /start -----------------
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    username = msg.from_user.username or f"user{msg.from_user.id}"
    add_user(username)

    # повідомлення всім адмінам про нового користувача
    for admin in get_all_admins():
        if admin != username:  # щоб самому собі не надсилало
            await bot.send_message(admin, f"🆕 Новий користувач зареєструвався: @{username}")

    await msg.answer(
        f"👋 Привіт, {username}!\n"
        "Ти можеш приєднатися до розіграшів через /join <id>\n"
        "Переглянути розіграші: /giveaways"
    )

# ----------------- /giveaways -----------------
@dp.message(Command("giveaways"))
async def cmd_giveaways(msg: types.Message):
    gvs = get_giveaways()
    if not gvs:
        await msg.answer("Немає активних розіграшів.")
        return
    response = "🎁 Активні розіграші:\n"
    for g in gvs:
        days_left = max(0, int((g[3] - int(time.time())) / 86400))
        response += f"ID: {g[0]} | {g[1]} | закінчення через {days_left} днів\n"
    await msg.answer(response)

# ----------------- /join -----------------
@dp.message(Command("join"))
async def cmd_join(msg: types.Message):
    username = msg.from_user.username or f"user{msg.from_user.id}"
    try:
        gid = int(msg.text.split()[1])
        g = get_giveaway_by_id(gid)
        if not g:
            await msg.answer("❌ Розіграш з таким ID не знайдено.")
            return
        join_giveaway(username, gid)
        await msg.answer(f"✅ Ви приєдналися до розіграшу: {g[1]}")
    except:
        await msg.answer("❌ Використання: /join <id>")

# ----------------- /ahelp (для адмінів) -----------------
@dp.message(Command("ahelp"))
async def cmd_ahelp(msg: types.Message):
    username = msg.from_user.username or f"user{msg.from_user.id}"
    if username not in get_all_admins():
        await msg.answer("❌ Ця команда доступна лише адміністраторам.")
        return
    commands = [
        "/ahelp — список команд адміністратора",
        "/creategiveaway <назва> <дні> — створити розіграш",
        "/participants <id> — список учасників розіграшу",
        "/winner <id> — обрати переможця",
        "/addadmin <username> — додати адміна",
        "/removeadmin <username> — видалити адміна",
        "/giveaways — перегляд розіграшів",
        "/reply <username> — відповісти користувачу"
    ]
    await msg.answer("⚙️ Доступні команди:\n" + "\n".join(commands))

# ----------------- Адмінські команди -----------------
@dp.message()
async def admin_commands(msg: types.Message):
    username = msg.from_user.username or f"user{msg.from_user.id}"
    if username not in get_all_admins():
        return

    text = msg.text
    args = text.split()

    if text.startswith("/creategiveaway"):
        if len(args) < 3:
            await msg.answer("❌ Використання: /creategiveaway <назва> <кількість днів>")
            return
        title = " ".join(args[1:-1])
        try:
            days = int(args[-1])
        except:
            await msg.answer("❌ Кількість днів має бути числом.")
            return
        end_time = int(time.time()) + days * 86400
        gid = create_giveaway(title, username, end_time)
        await msg.answer(f"🎁 Розіграш створено: {title} (ID: {gid})\nЗакінчення через {days} днів")
        for u in get_all_users():
            await bot.send_message(u, f"🎉 Новий розіграш: {title} (ID: {gid})!\nПриєднатись: /join {gid}\nЗакінчення через {days} днів")

    elif text.startswith("/participants"):
        if len(args) < 2:
            await msg.answer("❌ Використання: /participants <id>")
            return
        try:
            gid = int(args[1])
        except:
            await msg.answer("❌ ID має бути числом.")
            return
        participants = get_giveaway_participants(gid)
        await msg.answer(f"👥 Учасники ({len(participants)}):\n" + "\n".join(participants))

    elif text.startswith("/winner"):
        if len(args) < 2:
            await msg.answer("❌ Використання: /winner <id>")
            return
        try:
            gid = int(args[1])
        except:
            await msg.answer("❌ ID має бути числом.")
            return
        participants = get_giveaway_participants(gid)
        if not participants:
            await msg.answer("❌ Немає учасників.")
            return
        winner = random.choice(participants)
        await msg.answer(f"🏆 Переможець розіграшу {gid}: @{winner}")
        for u in participants:
            await bot.send_message(u, f"🏆 Переможець розіграшу {gid}: @{winner}")

    elif text.startswith("/addadmin"):
        if username != MAIN_ADMIN_USERNAME:
            await msg.answer("❌ Тільки головний адмін може додавати адміністраторів")
            return
        if len(args) < 2:
            await msg.answer("❌ Використання: /addadmin <username>")
            return
        new_admin = args[1].replace("@","")
        add_admin(new_admin)
        await msg.answer(f"✅ @{new_admin} додано як адміністратора")

    elif text.startswith("/removeadmin"):
        if username != MAIN_ADMIN_USERNAME:
            await msg.answer("❌ Тільки головний адмін може видаляти адміністраторів")
            return
        if len(args) < 2:
            await msg.answer("❌ Використання: /removeadmin <username>")
            return
        remove_admin(args[1].replace("@",""))
        await msg.answer(f"✅ @{args[1]} видалено з адмінів")

# ----------------- Запуск -----------------
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
