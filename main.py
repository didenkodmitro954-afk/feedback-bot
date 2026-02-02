import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from database import *

MAIN_ADMIN_ID = 1540349061
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

reply_mode = {}  # адмін відповідає користувачу

# Додати головного адміна
add_admin(MAIN_ADMIN_ID)

# ---------------- /start ----------------
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    username = msg.from_user.username or "NoName"

    # Перевіряємо, чи користувач новий
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id=?", (uid,))
    existing = cursor.fetchone()

    add_user(uid, username)

    # Якщо новий — повідомляємо адмінам
    if not existing:
        admins = get_all_admins()
        for admin in admins:
            await bot.send_message(
                admin,
                f"🆕 Новий користувач зареєструвався!\n👤 @{username}\n🆔 {uid}"
            )

    # Повідомлення користувачу
    await msg.answer(
        f"👋 Привіт, {username}!\n"
        "Ти можеш надіслати повідомлення, і наші адміни його отримають.\n"
        "Також можна приєднатись до розіграшів через /join <id>."
    )

# ---------------- /join ----------------
@dp.message(Command("join"))
async def cmd_join(msg: types.Message):
    uid = msg.from_user.id
    try:
        gid = int(msg.text.split()[1])
        join_giveaway(uid, gid)
        await msg.answer(f"🎉 Ти приєднався до розіграшу {gid}")
    except:
        await msg.answer("❌ Використовуй: /join <id>")

# ---------------- /giveaways ----------------
@dp.message(Command("giveaways"))
async def cmd_giveaways(msg: types.Message):
    gvs = get_giveaways()
    if not gvs:
        await msg.answer("Немає розіграшів")
        return
    response = "🎁 Розіграші:\n"
    for g in gvs:
        response += f"{g[0]}: {g[1]}\n"
    await msg.answer(response)

# ---------------- Повідомлення ----------------
@dp.message()
async def all_messages(msg: types.Message):
    uid = msg.from_user.id
    text = msg.text
    admins = get_all_admins()

    # Адмін відповідає користувачу
    if uid in reply_mode:
        target_uid = reply_mode[uid]
        await bot.send_message(target_uid, f"✉️ Від адміністратора:\n{text}")
        await msg.answer("✅ Відповідь надіслана")
        reply_mode.pop(uid)
        return

    # Адмінські команди
    if uid in admins:
        if text == "/ahelp":
            commands = [
                "/ahelp — показати список команд адміна",
                "/reply <id> — відповісти користувачу",
                "/giveaways — перегляд розіграшів"
            ]
            if uid == MAIN_ADMIN_ID:
                commands += [
                    "/addadmin <id> — додати адміна",
                    "/removeadmin <id> — видалити адміна",
                    "/create <назва> — створити розіграш"
                ]
            await msg.answer("⚙️ Доступні команди:\n" + "\n".join(commands))
            return

        if uid == MAIN_ADMIN_ID:
            if text.startswith("/addadmin"):
                try:
                    new_id = int(text.split()[1])
                    add_admin(new_id)
                    await msg.answer(f"✅ Користувач {new_id} став адміном")
                except:
                    await msg.answer("❌ Використовуй /addadmin <id> правильно")
                return

            if text.startswith("/removeadmin"):
                try:
                    rem_id = int(text.split()[1])
                    remove_admin(rem_id)
                    await msg.answer(f"✅ Адмін {rem_id} видалений")
                except:
                    await msg.answer("❌ Використовуй /removeadmin <id> правильно")
                return

            if text.startswith("/create"):
                title = text.replace("/create","").strip()
                if not title:
                    await msg.answer("❌ Вкажи назву розіграшу")
                    return
                create_giveaway(title)
                await msg.answer(f"🎁 Розіграш створено: {title}")
                return

        if text.startswith("/reply"):
            try:
                target = int(text.split()[1])
                reply_mode[uid] = target
                await msg.answer(f"✍️ Надішли текст для відповіді користувачу {target}")
            except:
                await msg.answer("❌ Використовуй /reply <id> правильно")
            return

    # Звичайне повідомлення користувача → надсилаємо всім адмінам
    if uid not in admins:
        for admin in admins:
            await bot.send_message(
                admin,
                f"📩 Повідомлення від @{msg.from_user.username or 'NoName'}\n🆔 {uid}\n\n{text}"
            )
        await msg.answer("✅ Повідомлення надіслано адміну")

# ---------------- Запуск ----------------
async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
