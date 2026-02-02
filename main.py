from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
import os

TOKEN = os.getenv("BOT_TOKEN")

# 🔴 ТИ — ГОЛОВНИЙ АДМІН (обовʼязково)
ADMINS = [123456789]  # ← ТУТ ТІЛЬКИ ТВІЙ ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ---------- КНОПКИ ----------

def main_menu(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📩 Написати адміну"))

    if user_id in ADMINS:
        kb.add(KeyboardButton("⚙️ Адмін панель"))

    return kb


def admin_panel():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("➕ Додати адміна"),
        KeyboardButton("📨 Повідомлення від користувачів"),
        KeyboardButton("⬅️ Назад")
    )
    return kb


# ---------- /start ----------

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer(
        "👋 Вітаю!",
        reply_markup=main_menu(msg.from_user.id)
    )


# ---------- КОРИСТУВАЧ → АДМІН ----------

@dp.message_handler(lambda m: m.text == "📩 Написати адміну")
async def write_admin(msg: types.Message):
    await msg.answer("✍️ Напиши повідомлення, я передам його адміну")


@dp.message_handler(lambda m: m.text not in [
    "⚙️ Адмін панель", "⬅️ Назад", "📨 Повідомлення від користувачів", "➕ Додати адміна"
])
async def forward_to_admin(msg: types.Message):
    for admin in ADMINS:
        await bot.send_message(
            admin,
            f"📩 Від @{msg.from_user.username or msg.from_user.id}:\n\n{msg
