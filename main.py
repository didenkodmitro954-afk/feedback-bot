import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from database import *

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ------------------ Кнопки ------------------
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
        KeyboardButton("📨 Повідомлення"),
        KeyboardButton("➕ Додати адміна"),
        KeyboardButton("📜 Лог дій"),
        KeyboardButton("🎁 Розіграші адмін")
    )
    kb.add(KeyboardButton("⬅️ Назад"))
    return kb

# ------------------ Стани ------------------
admin_mode = {}  # що зараз робить адмін
reply_mode = {}  # для відповіді конкретному користувачу

# ------------------ /start ------------------
@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username or "NoName")
    await msg.answer("👋 Вітаю! Вибери дію:", reply_markup=main_menu(msg.from_user.id))

# ------------------ Користувач → адміністратор ------------------
@dp.message_handler(lambda m: m.text == "📩 Написати адміну")
async def write_admin(msg: types.Message):
    await msg.answer("✍️ Напиши повідомлення, я передам адміну")

@dp.message_handler(lambda m: m.text not in [
    "⚙️ Адмін панель","⬅️ Назад","📨 Повідомлення","➕ Додати адміна",
    "📜 Лог дій","🎁 Розіграші адмін","🎁 Розіграші"
])
async def forward_to_admin(msg: types.Message):
    for admin in get_all_admins():
        await bot.send_message(
            admin,
            f"📩 Повідомлення від @{msg.from_user.username or 'без юза'}\n🆔 {msg.from_user.id}\n\n{msg.text}"
        )
    await msg.answer("✅ Повідомлення надіслано адміну")

# ------------------ Адмін панель ------------------
@dp.message_handler(lambda m: m.text == "⚙️ Адмін панель")
async def open_admin(msg: types.Message):
    if msg.from_user.id not in get_all_admins(): return
    await msg.answer("⚙️ Адмін панель", reply_markup=admin_panel())

@dp.message_handler(lambda m: m.text == "⬅️ Назад")
async def back(msg: types.Message):
    await msg.answer("🔙 Головне меню", reply_markup=main_menu(msg.from_user.id))
    admin_mode.pop(msg.from_user.id, None)

# ------------------ Додати адміна ------------------
@dp.message_handler(lambda m: m.text == "➕ Додати адміна")
async def add_admin_mode(msg: types.Message):
    if msg.from_user.id not in get_all_admins(): return
    admin_mode[msg.from_user.id] = "add_admin"
    await msg.answer("✍️ Введи ID користувача для призначення адміном:")

# ------------------ Лог дій ------------------
@dp.message_handler(lambda m: m.text == "📜 Лог дій")
async def show_logs(msg: types.Message):
    if msg.from_user.id not in get_all_admins(): return
    logs = get_logs()
    text = "📜 Останні дії адмінів:\n"
    for log in logs:
        text += f"{log[1]} → {log[2]} {log[3] or ''} ({log[4]})\n"
    await msg.answer(text or "Немає логів")

# ------------------ Розіграші ------------------
@dp.message_handler(lambda m: m.text in ["🎁 Розіграші","🎁 Розіграші адмін"])
async def giveaways(msg: types.Message):
    if msg.text == "🎁 Розіграші":
        gvs = get_giveaways()
        if not gvs: await msg.answer("Немає розіграшів")
        for g in gvs:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Участь", callback_data=f"join_{g[0]}"))
            await msg.answer(f"🎁 {g[1]}", reply_markup=kb)
    else:
        admin_mode[msg.from_user.id] = "create_giveaway"
        await msg.answer("✍️ Введи назву розіграшу:")

# ------------------ Callback для розіграшів ------------------
@dp.callback_query_handler(lambda c: c.data.startswith("join_"))
async def join_callback(c: types.CallbackQuery):
    gid = int(c.data.split("_")[1])
    join_giveaway(c.from_user.id, gid)
    await c.answer("Ти взяв участь у розіграші!")

# ------------------ Обробка вводу адміна ------------------
@dp.message_handler(lambda m: m.from_user.id in admin_mode)
async def admin_input(msg: types.Message):
    mode = admin_mode.get(msg.from_user.id)
    if mode == "add_admin":
        try:
            new_admin = int(msg.text)
            add_admin(new_admin)
            add_log(msg.from_user.id,"Додано адміна",target_user=new_admin)
            await msg.answer("✅ Користувач став адміном")
        except:
            await msg.answer("❌ Невірний ID")
    elif mode == "create_giveaway":
        create_giveaway(msg.text)
        add_log(msg.from_user.id,"Створено розіграш",info=msg.text)
        await msg.answer(f"🎁 Розіграш створено: {msg.text}")
    admin_mode.pop(msg.from_user.id)

# ------------------ Відповідь конкретному користувачу ------------------
@dp.message_handler(lambda m: m.text and m.from_user.id in reply_mode)
async def reply_user(msg: types.Message):
    uid = reply_mode[msg.from_user.id]
    await bot.send_message(uid,f"✉️ Від адміністратора:\n{msg.text}")
    add_log(msg.from_user.id,"Відповідь користувачу",target_user=uid,info=msg.text)
    await msg.answer("✅ Відповідь надіслана")
    reply_mode.pop(msg.from_user.id)

# ------------------ Запуск ------------------
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
