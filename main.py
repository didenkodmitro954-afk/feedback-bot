import os
import asyncio
from aiogram import Bot, Dispatcher, types
from database import *

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

reply_mode = {}  # якщо адмін відповідає користувачу

# ---------------- /start ----------------
@dp.message()
async def start_handler(msg: types.Message):
    uid = msg.from_user.id
    username = msg.from_user.username or "NoName"
    add_user(uid, username)

    admins = get_all_admins()
    # повідомлення адмінам про нового користувача
    for admin in admins:
        await bot.send_message(admin, f"🆕 Новий користувач зареєструвався:\n👤 @{username}\n🆔 {uid}")

    # повідомлення користувачу
    await msg.answer(
        f"👋 Привіт, {username}!\n"
        "Ти можеш надіслати мені повідомлення, і наші адміни його отримають.\n"
        "Напиши щось нижче ⬇️"
    )

# ---------------- Повідомлення ----------------
@dp.message()
async def message_handler(msg: types.Message):
    uid = msg.from_user.id
    admins = get_all_admins()
    text = msg.text

    # якщо адмін зараз відповідає користувачу
    if uid in reply_mode:
        target_uid = reply_mode[uid]
        await bot.send_message(target_uid, f"✉️ Від адміністратора:\n{text}")
        await msg.answer("✅ Відповідь надіслана")
        reply_mode.pop(uid)
        return

    # адмін-команди
    if uid in admins:
        if text == "/ahelp":
            await msg.answer(
                "⚙️ Список команд адміна:\n"
                "/ahelp — показати список команд\n"
                "/reply <id> — відповісти користувачу\n"
                "/addadmin <id> — додати адміна\n"
                "/removeadmin <id> — видалити адміна"
            )
            return

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

        if text.startswith("/reply"):
            try:
                target = int(text.split()[1])
                reply_mode[uid] = target
                await msg.answer(f"✍️ Надішли текст для відповіді користувачу {target}")
            except:
                await msg.answer("❌ Використовуй /reply <id> правильно")
            return

    # якщо звичайне повідомлення користувача → пересилаємо всім адмінам
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
