import os
import asyncio
from aiogram import Bot, Dispatcher, types
from database import *

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()  # v3

admin_mode = {}  # режим адміна для вводу ID або назви розіграшу

# ---------------- /start ----------------
@dp.message()
async def start_handler(msg: types.Message):
    if msg.text == "/start":
        add_user(msg.from_user.id, msg.from_user.username or "NoName")
        await msg.answer("👋 Вітаю! Використовуй команди:\n/giveaway — побачити розіграші")

# ---------------- /giveaway ----------------
@dp.message()
async def giveaway_handler(msg: types.Message):
    if msg.text == "/giveaway":
        gvs = get_giveaways()
        if not gvs:
            await msg.answer("Немає розіграшів")
            return
        response = "🎁 Розіграші:\n"
        for g in gvs:
            response += f"{g[0]}: {g[1]} — приєднатися: /join{g[0]}\n"
        await msg.answer(response)

# ---------------- /join<ID> ----------------
@dp.message()
async def join_handler(msg: types.Message):
    if msg.text.startswith("/join"):
        try:
            gid = int(msg.text.replace("/join",""))
            join_giveaway(msg.from_user.id, gid)
            await msg.answer(f"✅ Ти приєднався до розіграшу {gid}")
        except:
            await msg.answer("❌ Невірний розіграш")

# ---------------- Адмін-команди ----------------
@dp.message()
async def admin_handler(msg: types.Message):
    uid = msg.from_user.id
    admins = get_all_admins()

    if uid not in admins:
        return

    text = msg.text

    # список адмін-команд
    if text == "/ahelp":
        help_text = (
            "/ahelp — список команд адміна\n"
            "/addadmin <id> — додати адміна\n"
            "/removeadmin <id> — видалити адміна\n"
            "/create <назва> — створити розіграш\n"
        )
        await msg.answer(help_text)
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

    if text.startswith("/create"):
        try:
            title = text.replace("/create","").strip()
            if not title:
                await msg.answer("❌ Вкажи назву розіграшу")
                return
            create_giveaway(title)
            await msg.answer(f"🎁 Розіграш створено: {title}")
        except:
            await msg.answer("❌ Сталася помилка")
