import asyncio
import logging
import re
import html
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError
from dotenv import load_dotenv

load_dotenv()


def get_bot_token() -> str:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylga BOT_TOKEN kiriting.")
    return token


def get_group_id() -> int | None:
    group_id_raw = os.getenv("GROUP_ID", "").strip()
    if not group_id_raw:
        return None
    try:
        return int(group_id_raw)
    except ValueError as err:
        raise RuntimeError("GROUP_ID butun son bo'lishi kerak. Masalan: -1001234567890") from err


TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROUP_ID = get_group_id()
bot = Bot(token=TOKEN)
dp = Dispatcher()


def normalize_phone(raw_phone: str) -> str:
    source = raw_phone.strip()
    digits = re.sub(r"\D", "", source)
    if not digits:
        raise ValueError("Telefon raqamda kamida bitta raqam bo'lishi kerak.")
    if source.startswith("+"):
        return f"+{digits}"
    if digits.startswith("00"):
        return f"+{digits[2:]}"
    return f"+{digits}"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚕 Buyurtma berish")],
            [KeyboardButton(text="ℹ️ Qo'llanma")]
        ],
        resize_keyboard=True
    )


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Telefon raqamini yuborish 📱", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


# Holatlar (States)
class OrderTaxi(StatesGroup):
    details = State()  # Qayerdan-qayerga, necha kishi, soat
    phone = State()  # Telefon raqami


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! Taksi buyurtma qilish botiga xush kelibsiz.\n\n"
        "Buyurtma berish uchun pastdagi tugmadan foydalaning.",
        reply_markup=main_menu_keyboard()
    )
    await message.answer(
        "📌 Qo'llanma:\n"
        "1) '🚕 Buyurtma berish' tugmasini bosing\n"
        "2) Buyurtmangizni o'zingiz xohlagan uslubda yozing\n"
        "3) Telefon raqamingizni yuboring\n\n"
        "📝 Misollar:\n"
        "• Andijonga 1 kishi 10 da ketmoqchiman, oldi bo'sh bo'lsin\n"
        "• Andijonga ketaman\n"
        "• Farg'onadan Toshkentga 2 kishi bugun 21:00"
    )


@dp.message(F.text == "ℹ️ Qo'llanma")
async def show_guide(message: Message):
    await message.answer(
        "📖 Botdan foydalanish:\n\n"
        "1️⃣ '🚕 Buyurtma berish' tugmasini bosing\n"
        "2️⃣ Qayerga, nechta kishi va vaqtni oddiy xabar qilib yozing\n"
        "3️⃣ Telefon raqamingizni yuboring\n"
        "4️⃣ Buyurtmangiz haydovchilarga yuboriladi\n\n"
        "✅ Siz xohlagancha yozishingiz mumkin.\n\n"
        "📝 Misollar:\n"
        "• Toshkentga 1 kishi 10 da ketmoqchiman\n"
        "Tayyor bo'lsangiz, '🚕 Buyurtma berish' ni bosing.",
        reply_markup=main_menu_keyboard()
    )

@dp.message(F.text == "🚕 Buyurtma berish")
async def start_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Buyurtmangizni bitta xabarda yozing (erkin formatda):\n\n"
        "• Toshkentga 1 kishi 10 da ketmoqchiman\n",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(OrderTaxi.details)



@dp.message(OrderTaxi.details)
async def process_details(message: Message, state: FSMContext):
    details_text = (message.text or "").strip()
    if not details_text:
        await message.answer(
            "Iltimos, buyurtmangizni matn ko'rinishida yozing.\n"
            "Masalan: Andijonga 1 kishi 10 da ketmoqchiman"
        )
        return

    await state.update_data(details=details_text)
    await message.answer(
        "Iltimos, telefon raqamingizni yuboring (masalan: +998901234567):",
        reply_markup=phone_keyboard()
    )
    await state.set_state(OrderTaxi.phone)


@dp.message(OrderTaxi.phone)
async def process_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text or ""

    try:
        phone = normalize_phone(phone)
    except ValueError as err:
        await message.answer(
            f"{err}\nQayta kiriting. Masalan: +998901234567",
            reply_markup=phone_keyboard()
        )
        return

    data = await state.get_data()
    details = data.get("details", "")

    user_id = message.from_user.id
    user_name = html.escape(message.from_user.full_name)
    if message.from_user.username:
        user_link = f"<a href='tg://user?id={user_id}'>{user_name}</a> (@{html.escape(message.from_user.username)})"
    else:
        user_link = f"<a href='tg://user?id={user_id}'>{user_name}</a>"

    order_text = (
        f"Mijoz: {user_link}\n"
        f"Buyurtma: {html.escape(details)}\n\n"
        f"Telefon: <a href='tel:{phone}'>{phone}</a>"
    )

    target_chat = GROUP_ID if GROUP_ID else message.chat.id

    try:
        await bot.send_message(chat_id=target_chat, text=order_text, parse_mode="HTML")
        await message.answer(
            "Sizning buyurtmangiz haydovchilarga yuborildi! ✅\n"
            "Tez orada siz bilan bog'lanishadi 📞\n\n"
            "Yangi buyurtma uchun '🚕 Buyurtma berish' tugmasini bosing.",
            reply_markup=main_menu_keyboard()
        )
    except TelegramAPIError as err:
        await message.answer(
            f"Xatolik yuz berdi: {err}\n"
            "Qayta urinib ko'ring yoki /start bosing.",
            reply_markup=main_menu_keyboard()
        )

    await state.clear()


async def main():
    logging.basicConfig(level=logging.INFO)
    global bot

    token = get_bot_token()
    bot = Bot(token=token)

    try:
        await dp.start_polling(bot)
    except TelegramNetworkError as err:
        logging.exception("Telegram server bilan bog'lanishda xatolik yuz berdi: %s", err)
        raise SystemExit(f"Telegramga ulanib bo'lmadi: {err}") from err


if __name__ == "__main__":
    asyncio.run(main())
