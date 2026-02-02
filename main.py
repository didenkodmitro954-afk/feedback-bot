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
    if msg.text == "/start":
        uid = msg.from_user.id
        username = msg.from_user.username or "NoName"
        add_user(uid, username)

        # повідомляємо всім адмінам
        admins = get_all_admins()
        for admin in admins:
            await bot.send_message(admin, f"🆕 Новий користувач зареєструвався:\n👤 @{username}\n🆔 {uid}")

        await msg.answer(
            f"👋 Привіт, {username}!\n"
            "Ти можеш надіслати повідомлення адміну нижче ⬇️"
        )

# ---------------- Повідомлення ----------------
@dp.message()
async def message_handler(msg: types.Message):
    uid = msg.from_user.id
    text = msg.text
    admins = get_all_admins()

    # якщо адмін зараз відповідає користувачу
    if uid in reply_mode:
        target_uid = reply_mode[uid]
        await bot.send_message(target_uid, f"✉️ Від адміністратора:\n{text}")
        await msg.answer("✅ Відповідь надіслана")
        reply_mode.pop(uid)
        return

    # Адмін-команди
    if uid in admins:
        if text == "/ahelp":
            await msg.answer(
                "⚙️ Список команд адміна:\n"
                "/ahelp — показати список команд адміна\n"
                "/addadmin <id> — додати адміна\n"
                "/removeadmin <id> — видалити адміна\n"
                "/reply <id> — відповісти користувачу\n"
                "/create <назва> — створити розіграш\n"
                "/giveaways — список розіграшів\n"
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

        if text.startswith("/create"):
            title = text.replace("/create","").strip()
            if not title:
                await msg.answer("❌ Вкажи назву розіграшу")
                return
            create_giveaway(title)
            await msg.answer(f"🎁 Розіграш створено: {title}")
            return

        if text == "/giveaways":
            gvs = get_giveaways()
            if not gvs:
                await msg.answer("Немає розіграшів")
                return
            response = "🎁 Розіграші:\n"
            for g in gvs:
                response += f"{g[0]}: {g[1]}\n"
            await msg.answer(response)
            return

    # Звичайне повідомлення користувача → пересилаємо всім адмінам
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
