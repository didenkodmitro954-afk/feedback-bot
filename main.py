import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# Змінні з середовища
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Перевірка, чи змінні задані
if not TOKEN or not ADMIN_ID:
    raise Exception("BOT_TOKEN або ADMIN_ID не задано у Variables!")

ADMIN_ID = int(ADMIN_ID)

# Створюємо бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Вітаємо!\n\n"
        "Це бот для замовлень та зворотного зв’язку.\n"
        "Напиши повідомлення — адміністратор його отримає."
    )

@dp.message()
async def feedback(message: types.Message):
    text = (
        f"🆕 НОВЕ ПОВІДОМЛЕННЯ\n\n"
        f"👤 Користувач: @{message.from_user.username}\n"
        f"🆔 ID: {message.from_user.id}\n\n"
        f"💬 Повідомлення:\n{message.text}"
    )
    await bot.send_message(ADMIN_ID, text)
    await message.answer("✅ Ваше повідомлення надіслано адміну!")

async def main():
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

from database import add_user, get_balance, update_balance

@dp.message(CommandStart())
async def start(message: types.Message):
    # Реєструємо користувача в базі
    add_user(message.from_user.id, message.from_user.username or "NoName")
    
    await message.answer(
        f"👋 Привіт, @{message.from_user.username}!\n"
        f"Ваш баланс: {get_balance(message.from_user.id)} монет.\n"
        "Напиши повідомлення — адміністратор його отримає."
    )
