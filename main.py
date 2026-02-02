import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

from database import add_user, get_balance

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()


# 🔹 /start
@dp.message(CommandStart())
async def start(message: types.Message):
    add_user(message.from_user.id, message.from_user.username or "NoName")

    await message.answer(
        f"👋 Привіт!\n"
        f"💰 Баланс: {get_balance(message.from_user.id)}\n\n"
        "✉️ Напиши повідомлення — адміністратор відповість."
    )


# 🔹 Повідомлення від КОРИСТУВАЧА → адміну
@dp.message(lambda msg: msg.from_user.id != ADMIN_ID)
async def user_to_admin(message: types.Message):
    await bot.send_message(
        ADMIN_ID,
        f"📩 НОВЕ ПОВІДОМЛЕННЯ\n\n"
        f"👤 @{message.from_user.username}\n"
        f"🆔 ID: {message.from_user.id}\n\n"
        f"{message.text}"
    )
    await message.answer("✅ Повідомлення надіслано адміну!")


# 🔹 Відповідь АДМІНА користувачу
@dp.message(lambda msg: msg.from_user.id == ADMIN_ID)
async def admin_reply(message: types.Message):
    try:
        user_id, text = message.text.split(" ", 1)
        await bot.send_message(int(user_id), f"✉️ Від адміністратора:\n{text}")
        await message.answer("✅ Відповідь надіслано")
    except:
        await message.answer("❌ Формат: ID текст")


async def main():
    print("Bot started")
    await dp.start_polling(bot)


if name == "main":
    asyncio.run(main())
