from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher import filters
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import logging
from config import BOT_TOKEN, REQUIRED_CHANNEL

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)

user_languages = {}
user_warnings = {}

class AdminFilter(BoundFilter):
    key = 'is_admin'

    async def check(self, message: types.Message):
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.is_chat_admin()

dp.filters_factory.bind(AdminFilter)

async def is_subscribed(user_id):
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

@dp.message_handler(commands=['start'])
async def start_cmd(msg: types.Message):
    user_id = msg.from_user.id
    if not await is_subscribed(user_id):
        markup = InlineKeyboardMarkup().add(
            InlineKeyboardButton("📢 Obuna bo‘lish", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}")
        )
        await msg.answer("❌ Botdan foydalanish uchun kanalga obuna bo‘ling:", reply_markup=markup)
        return

    lang_markup = InlineKeyboardMarkup(row_width=2)
    lang_markup.add(
        InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    )
    await msg.answer("🌐 Tilni tanlang:

Выберите язык:", reply_markup=lang_markup)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("lang_"))
async def set_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split("_")[1]
    user_languages[callback_query.from_user.id] = lang
    text = "✅ Til tanlandi!" if lang == "uz" else "✅ Язык выбран!"
    await callback_query.message.edit_text(text)

@dp.message_handler(content_types=types.ContentType.TEXT)
async def check_ads(msg: types.Message):
    if msg.chat.type not in ["group", "supergroup"]:
        return

    user_id = msg.from_user.id
    text = msg.text.strip().lower()

    if user_id not in user_warnings:
        user_warnings[user_id] = {}

    if text in user_warnings[user_id]:
        user_warnings[user_id][text] += 1
    else:
        user_warnings[user_id][text] = 1

    if user_warnings[user_id][text] > 1:
        try:
            await bot.restrict_chat_member(msg.chat.id, user_id, types.ChatPermissions(can_send_messages=False), until_date=259200)
            await msg.reply("🚫 Siz 1 xil reklamani qayta-qayta yubordingiz. 72 soatga yozolmaysiz.")
        except:
            pass

@dp.message_handler(commands=['takror'], is_admin=True)
async def repeat_msg(msg: types.Message):
    await msg.answer("🔁 Takroriy xabarlar funksiyasi faollashtirilgan (namunaviy buyruq).")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
