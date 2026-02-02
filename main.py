import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from database import *

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

bot = Bot(token=TOKEN)
dp = Dispatcher()

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
@dp.message(Command("start"))
async def start_handler(msg: types.Message):
    add_user(msg.from_user.id, msg.from_user.username or "NoName")
    await msg.answer("👋 Вітаю! Вибери дію:", reply_markup=main_menu(msg.from_user.id))
    # повідомлення адмінам про нового користувача
    for admin in get_all_admins():
        try:
            await bot.send_message(
                admin,
                f"🆕 Новий користувач:\n👤 @{msg.from_user.username or 'NoName'}\n🆔 {msg.from_user.id}"
            )
        except Exception as e:
            print(f"Не вдалося відправити сповіщення адміну {admin}: {e}")

# ---------------- Обробка кнопок ----------------
@dp.message()
async def buttons_handler(msg: types.Message):
    text = msg.text
    uid = msg.from_user.id
    admins = get_all_admins()

    # Адмін-панель
    if text == "⚙️ Адмін панель" and uid in admins:
        await msg.answer("⚙️ Адмін панель", reply_markup=admin_panel())
        return

    if text == "⬅️ Назад" and uid in admins:
        await msg.answer("🔙 Головне меню", reply_markup=main_menu(uid))
        admin_mode.pop(uid, None)
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

    if text == "📩 Повідомлення" and uid in admins:
        # Тут має бути логіка для перегляду повідомлень
        await msg.answer("Функція перегляду повідомлень ще не реалізована")
        return

    if text == "🎁 Розіграші":
        gvs = get_giveaways()
        if not gvs:
            await msg.answer("Наразі немає активних розіграшів")
            return
        for g in gvs:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Участь", callback_data=f"join_{g[0]}")]
            ])
            await msg.answer(f"🎁 Розіграш: {g[1]}", reply_markup=kb)
        return

    if text == "📩 Написати адміну":
        await msg.answer("Напишіть ваше повідомлення, і я передам його адміністраторам")
        return

    # Відповідь адміна користувачу
    if uid in reply_mode:
        target_uid = reply_mode[uid]
        try:
            await bot.send_message(target_uid, f"✉️ Від адміністратора:\n{text}")
            await msg.answer("✅ Відповідь надіслана")
        except Exception as e:
            await msg.answer(f"❌ Не вдалося відправити повідомлення: {e}")
        reply_mode.pop(uid, None)
        return

    # Режим admin_mode
    if uid in admin_mode:
        mode = admin_mode[uid]
        if mode == "add_admin":
            try:
                new_admin_id = int(text)
                add_admin(new_admin_id)
                await msg.answer("✅ Користувач став адміном")
            except ValueError:
                await msg.answer("❌ Невірний формат ID. ID має бути числом")
            except Exception as e:
                await msg.answer(f"❌ Помилка при додаванні адміна: {e}")
            admin_mode.pop(uid, None)
            return
        elif mode == "remove_admin":
            try:
                remove_admin_id = int(text)
                remove_admin(remove_admin_id)
                await msg.answer("✅ Адмін видалений")
            except ValueError:
                await msg.answer("❌ Невірний формат ID. ID має бути числом")
            except Exception as e:
                await msg.answer(f"❌ Помилка при видаленні адміна: {e}")
            admin_mode.pop(uid, None)
            return
        elif mode == "create_giveaway":
            if text.strip():
                create_giveaway(text.strip())
                await msg.answer(f"🎁 Розіграш створено: {text}")
                admin_mode.pop(uid, None)
            else:
                await msg.answer("❌ Назва розіграшу не може бути порожньою")
            return

    # Повідомлення від користувача адмінам
    if uid not in admins and text and text.strip():
        user_info = f"📩 Повідомлення від @{msg.from_user.username or 'NoName'}\n🆔 {uid}\n\n{text}"
        admin_sent = False
        for admin in admins:
            try:
                await bot.send_message(admin, user_info)
                admin_sent = True
            except Exception as e:
                print(f"Не вдалося відправити повідомлення адміну {admin}: {e}")
        
        if admin_sent:
            await msg.answer("✅ Повідомлення надіслано адміністраторам")
        else:
            await msg.answer("❌ Не вдалося відправити повідомлення адміністраторам")
        return

    # Якщо жодна з умов не виконалася
    if uid in admins:
        await msg.answer("Оберіть дію з меню", reply_markup=admin_panel())
    else:
        await msg.answer("Оберіть дію з меню", reply_markup=main_menu(uid))

# ---------------- Callback для розіграшів ----------------
@dp.callback_query()
async def giveaway_callback(c: types.CallbackQuery):
    if c.data.startswith("join_"):
        try:
            gid = int(c.data.split("_")[1])
            join_giveaway(c.from_user.id, gid)
            await c.answer("✅ Ти взяв участь у розіграші!", show_alert=False)
        except ValueError:
            await c.answer("❌ Помилка: невірний ідентифікатор розіграшу")
        except Exception as e:
            await c.answer(f"❌ Помилка: {str(e)}")
    else:
        await c.answer("Невідома команда")

# ---------------- Запуск ----------------
async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
