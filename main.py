import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from database import *

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()  # v3: dispatcher без аргументів

# ---------------- Кнопки ----------------
def main_menu(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📩 Написати адміну"))
    kb.add(KeyboardButton("🎁 Розіграші"))
    if user_id in get_all_admins():
        kb.add(KeyboardButton("⚙️ Адмін панель"))
    return kb

def admin_panel():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📩 Повідомлення"),
        KeyboardButton("➕ Додати адміна"),
        KeyboardButton("➖ Видалити адміна"),
        KeyboardButton("🎁 Розіграші адмін")
    )
    kb.add(KeyboardButton("⬅️ Назад"))
    return kb

# ---------------- Стани ----------------
admin_mode = {}  # що робить адмін зараз
reply_mode = {}  # відповіді користувачам

# ---------------- /start ----------------
@dp.message()
async def start_handler(msg: types.Message):
    if msg.text == "/start":
        add_user(msg.from_user.id, msg.from_user.username or "NoName")
        await msg.answer("👋 Вітаю! Вибери дію:", reply_markup=main_menu(msg.from_user.id))
        # повідомлення адмінам про нового користувача
        for admin in get_all_admins():
            await bot.send_message(admin,
                                   f"🆕 Новий користувач:\n👤 @{msg.from_user.username or 'NoName'}\n🆔 {msg.from_user.id}")

# ---------------- Обробка кнопок ----------------
@dp.message()
async def buttons_handler(msg: types.Message):
    text = msg.text
    uid = msg.from_user.id
    admins = get_all_admins()

    system_buttons = ["⚙️ Адмін панель","⬅️ Назад","📩 Повідомлення","➕ Додати адміна",
                      "➖ Видалити адміна","🎁 Розіграші адмін","🎁 Розіграші","📩 Написати адміну"]

    # Адмін-панель
    if text == "⚙️ Адмін панель" and uid in admins:
        await msg.answer("⚙️ Адмін панель", reply_markup=admin_panel())
        return

    if text == "⬅️ Назад" and uid in admins:
        await msg.answer("🔙 Головне меню", reply_markup=main_menu(uid))
        admin_mode.pop(uid,None)
        return

    if text == "➕ Додати адміна" and uid in admins:
        admin_mode[uid] = "add_admin"
        await msg.answer("✍️ Введи ID користувача для призначення адміном")
        return

    if text == "➖ Видалити адміна" and uid in admins:
        admin_mode[uid] = "remove_admin"
        await msg.answer("✍️ Введи ID адміна для видалення")
        return

    if text == "🎁 Розіграші адмін" and uid in admins:
        admin_mode[uid] = "create_giveaway"
        await msg.answer("✍️ Введи назву розіграшу")
        return

    if text == "🎁 Розіграші" and uid not in admins:
        gvs = get_giveaways()
        if not gvs:
            await msg.answer("Немає розіграшів")
        for g in gvs:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Участь", callback_data=f"join_{g[0]}"))
            await msg.answer(f"🎁 {g[1]}", reply_markup=kb)
        return

    # Всі інші повідомлення
    if text not in system_buttons:
        # Відповідь адміна користувачу
        if uid in reply_mode:
            target_uid = reply_mode[uid]
            await bot.send_message(target_uid,f"✉️ Від адміністратора:\n{text}")
            await msg.answer("✅ Відповідь надіслана")
            reply_mode.pop(uid)
            return

        # Режим admin_mode
        if uid in admin_mode:
            mode = admin_mode[uid]
            if mode == "add_admin":
                try:
                    add_admin(int(text))
                    await msg.answer("✅ Користувач став адміном")
                except:
                    await msg.answer("❌ Невірний ID")
                admin_mode.pop(uid)
                return
            elif mode == "remove_admin":
                try:
                    remove_admin(int(text))
                    await msg.answer("✅ Адмін видалений")
                except:
                    await msg.answer("❌ Невірний ID")
                admin_mode.pop(uid)
                return
            elif mode == "create_giveaway":
                create_giveaway(text)
                await msg.answer(f"🎁 Розіграш створено: {text}")
                admin_mode.pop(uid)
                return

        # Повідомлення адмінам
        for admin in admins:
            await bot.send_message(admin,
                                   f"📩 Повідомлення від @{msg.from_user.username or 'NoName'}\n🆔 {uid}\n\n{text}")
        await msg.answer("✅ Повідомлення надіслано адміну")

# ---------------- Callback для розіграшів ----------------
@dp.callback_query()
async def giveaway_callback(c: types.CallbackQuery):
    if c.data.startswith("join_"):
        gid = int(c.data.split("_")[1])
        join_giveaway(c.from_user.id, gid)
        await c.answer("Ти взяв участь у розіграші!")

# ---------------- Запуск ----------------
async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
