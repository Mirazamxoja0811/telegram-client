from pyrogram import Client, filters, enums, idle
import pyrogram.utils
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999

import asyncio
import re
import os
import html
import time
from collections import OrderedDict
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
bot_sender = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

# Dublikatlarni ushlash keshi (30 daqiqalik xotira)
RECENT_MESSAGES = OrderedDict()  # key: hash/phone, value: timestamp
DUPLICATE_CACHE_TTL = 1800  # 30 daqiqa (soniyalarda)
MAX_CACHE_SIZE = 300


def clean_duplicate_cache():
    now = time.time()
    keys_to_remove = [k for k, v in RECENT_MESSAGES.items() if now - v > DUPLICATE_CACHE_TTL]
    for k in keys_to_remove:
        del RECENT_MESSAGES[k]


def is_duplicate(text: str, phone: str | None) -> bool:
    clean_duplicate_cache()
    now = time.time()

    # Telefon raqami bo'yicha takroriylikni tekshirish
    if phone and phone in RECENT_MESSAGES:
        return True

    # Xabar matnining boshlang'ich 60 ta belgisini tekshirish
    norm_text = re.sub(r"\s+", " ", text.strip().lower())[:60]
    text_key = f"txt:{norm_text}"
    if text_key in RECENT_MESSAGES:
        return True

    # Yangi xabar va telefonni keshga qo'shish
    if phone:
        RECENT_MESSAGES[phone] = now
    RECENT_MESSAGES[text_key] = now

    # Kesh hajmini cheklash
    while len(RECENT_MESSAGES) > MAX_CACHE_SIZE:
        RECENT_MESSAGES.popitem(last=False)

    return False


def get_api_id() -> int:
    api_id_raw = os.getenv("API_ID", "").strip()
    if not api_id_raw:
        raise RuntimeError("API_ID topilmadi. .env faylga API_ID kiriting.")
    try:
        return int(api_id_raw)
    except ValueError as err:
        raise RuntimeError("API_ID butun son bo'lishi kerak.") from err


def get_api_hash() -> str:
    api_hash = os.getenv("API_HASH", "").strip()
    if not api_hash:
        raise RuntimeError("API_HASH topilmadi. .env faylga API_HASH kiriting.")
    return api_hash


def parse_target_group(raw: str):
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith("@"):
        return raw
    try:
        return int(raw)
    except ValueError:
        return raw


API_ID = get_api_id()
API_HASH = get_api_hash()
TARGET_GROUP_ID = parse_target_group(os.getenv("TARGET_GROUP_ID", ""))


def build_app():
    session_string = os.getenv("USERBOT_SESSION_STRING", "").strip()
    if session_string:
        return Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=session_string)

    session_name = os.getenv("USERBOT_SESSION_NAME", "my_account").strip() or "my_account"
    session_dir = os.path.dirname(session_name)
    if session_dir:
        os.makedirs(session_dir, exist_ok=True)
    return Client(session_name, api_id=API_ID, api_hash=API_HASH)


app = build_app()

# Toshkent va Andijon shaharlari hamda tumanlari (Lotin va Kirill alifbosida)
CITIES = [
    # --- Toshkent va Toshkent viloyati ---
    # Lotincha:
    "toshkent", "tashkent", "yunusobod", "chilonzor", "yakkasaroy", "mirobod", 
    "mirzo ulug'bek", "mirzo ulugbek", "sergeli", "yangihayot", "olmazor", "uchtepa", 
    "bektemir", "yashnobod", "quyliq", "qo'yliq", "qoyliq", "angren", "olmaliq", 
    "chirchiq", "pskent", "bo'ka", "boka", "chinoz", "yangiyo'l", "yangiyol", 
    "g'azalkent", "gazalkent", "parkent", "zangiota", "qibray",
    # Kirillcha:
    "тошкент", "ташкент", "юнусобод", "чилонзор", "яккасарой", "миробод", 
    "мирзо улуғбек", "мирзо улугбек", "сергели", "янгиҳаёт", "янгихаёт", "олмазор", 
    "учтепа", "бектемир", "яшнобод", "қўйлиқ", "койлик", "ангрен", "олмалиқ", 
    "чирчиқ", "пскент", "бўка", "бука", "чиноз", "янгийўл", "янгиюл", 
    "ғазалкент", "газалкент", "паркент", "зангиота", "қибрай",

    # --- Andijon viloyati va tumanlari ---
    # Lotincha:
    "andijon", "andijan", "xonobod", "qorasuv", "qo'rg'ontepa", "qorgontepa", 
    "qurgontepa", "shahrixon", "shaxrixon", "asaka", "marhamat", "buloqboshi", 
    "paxtaobod", "pahtaobod", "izboskan", "poytug'", "poytug", "jalaquduq", 
    "jalamudoq", "baliqchi", "ulug'nor", "ulugnor", "bo'ston", "boston", "bo'z", "boz",
    "xo'jaobod", "xojaobod", "do'stlik", "dostlik", "tamojni", "tamozhni",
    # Kirillcha:
    "андижон", "андижан", "хонобод", "қорасув", "корасув", "қўрғонтепа", 
    "коргаンテпа", "кургаンテпа", "шаҳрихон", "шахрихон", "асака", "марҳамат", 
    "мархамат", "булоқбоши", "булокбоши", "пахтаобод", "избоскан", "пойтуғ", 
    "пойтуг", "жалақудуқ", "жалакудук", "балиқчи", "улуғнор", "улугнор", 
    "бўстон", "бустон", "бўз", "буз", "хожаобод", "хўжаобод", "дўстлик", "дустлик", "таможни", "таможня",

    # --- Vodiy, Qamchiq dovoni va qo'shni shaharlar ---
    # Lotincha:
    "vodiy", "qamchiq", "dovon", "qo'qon", "qoqon", "kokand", "namangan", 
    "farg'ona", "fargona", "marg'ilon", "margilon", "rishton", "yozoyovon", "quva",
    # Kirillcha:
    "водий", "қамчиқ", "камчик", "довон", "қўқон", "қоқон", "коканд", "наманган", 
    "фарғона", "фаргона", "марғилон", "маргилон", "риштон", "ёзёвон", "қува"
]

# Taksiga oid kalit so'zlar (Lotin va Kirill alifbosida)
KEYWORDS = [
    # Lotincha:
    "kishi", "odam", "bor", "pochta", "poshta", "ketyapman", "ketaman", "ketmoqchiman",
    "boraman", "bormoqchiman", "beraman", "ming", "som", "so'm", "kerak", "oladigan", "taksi",
    # Kirillcha:
    "киши", "одам", "бор", "почта", "пошта", "кетяпман", "кетаман", "кетмокчиман", 
    "кетмоқчиман", "бораман", "бормокчиман", "бормоқчиман", "бераман", "минг", "сум", 
    "сўм", "керак", "оладиган", "такси"
]

# Haydovchilar (Taksistlar) uchun taqiqlangan so'zlar (Stop-words - Lotin va Kirill)
DRIVER_KEYWORDS = [
    # Mashina nomlari va modellar (Lotin va Kirill)
    "moshina", "mashina", "cobalt", "kobilt", "kőbilt", "koblt", "kobl", "gentra", "jentra",
    "nexia", "neksiya", "spark", "damas", "malibu", "tracker", "lasetti", "lacetti",
    "labo", "byd", "chazor", "avto", "auto", "taksidaman", "taksist", "haydovchiman",
    "мошина", "машина", "кобальт", "кобильт", "коблт", "кобл", "жентра", "джентра", "нексия", "спарк",
    "дамас", "малибу", "трекер", "ласетти", "лабо", "таксидаман", "таксист", "хайдовчиман",
    # Haydovchi iboralari va bo'sh joylar (Lotin va Kirill)
    "odam kam", "kishi kam", "ta kam", "ga kam", "joy bor", "bosh joy", "bo'sh joy", "joyim bor",
    "odam olaman", "pochta olaman", "pochtalar olaman", "yuk olaman", "chiqamiz", "yuraman", "ketyapmiz",
    "tayyor moshina", "moshina tayyor", "yuradigan moshina", "taksi bor", "pokiza", "kurgavoy", "tarnirovka", "tonirovka",
    "srochno", "yuramiz", "srochno yuramiz", "olamiz",
    "одам кам", "киши кам", "та кам", "га кам", "жой бор", "бош жой", "бўш жой", "жойим бор",
    "одам оламан", "почта оламан", "почталар оламан", "почта оламиз", "почталар оламиз", "yuk olamiz", "юк оламиз", "одам оламиз", "оламиз",
    "чиқамиз", "юраманг", "юраман", "юрамиз", "кетяпмиз", "срочно", "срочно юрамиз",
    "тайёр мошина", "мошина тайёр", "такси бор", "покиза", "кургавой", "тарнировка", "тонировка"
]

# Qo'shimcha haydovchi iboralarining muntazam ifodalari (Regex)
DRIVER_REGEXES = [
    r"\b\d+[\s\.\,]*га[\s\.\,]*\d+[\s\.\,]*кам\b",
    r"\b\d+[\s\.\,]*га[\s\.\,]*кам\b",
    r"\b\d+[\s\.\,]*та[\s\.\,]*кам\b",
    r"\b\d+[\s\.\,]*кам\b",
    r"\b(га|та)?\s*\d+\s*кам\b",
    r"\bсрочно\s+юрамиз\b",
    r"\bsrochno\s+yuramiz\b",
    r"\bпочта(лар)?\s+оламиз\b",
    r"\bpochta(lar)?\s+olamiz\b",
]


def is_driver_message(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    
    # Harflar orasiga probel qo'yilgan matnlarni normalizatsiya qilish (masalan: "К О Б Л Т" -> "КОБЛТ")
    text_normalized = re.sub(r'(?<=\b\w)\s+(?=\w\b)', '', text_lower)

    # 1. Kalit so'zlar bo'yicha tekshirish
    for kw in DRIVER_KEYWORDS:
        if kw in text_lower or kw in text_normalized:
            return True

    # 2. Regex andozalari bo'yicha tekshirish ("2 КАМ", "ГА 2 КАМ", "СРОЧНО ЮРАМИЗ")
    for pattern in DRIVER_REGEXES:
        if re.search(pattern, text_lower, re.IGNORECASE) or re.search(pattern, text_normalized, re.IGNORECASE):
            return True

    return False


def is_taxi_request(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()

    # Agar haydovchi so'zlari bo'lsa -> mijoz emas!
    if is_driver_message(text):
        return False

    # Matn ichida hech bo'lmaganda 1 ta shahar nomi...
    has_city = any(city in text_lower for city in CITIES)
    # va 1 ta taksiga oid so'z qatnashganligini tekshirish
    has_keyword = any(keyword in text_lower for keyword in KEYWORDS)

    return has_city and has_keyword


def extract_phone(text: str) -> str | None:
    if not text:
        return None
    pattern = r"(\+?998[\s\-]?\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\b998\d{9}\b|\b\d{9}\b|\b\d{2}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b)"
    match = re.search(pattern, text)
    if match:
        raw_num = match.group(0)
        digits = re.sub(r"\D", "", raw_num)
        if len(digits) == 9:
            return f"+998{digits}"
        elif len(digits) == 12 and digits.startswith("998"):
            return f"+{digits}"
    return None


@app.on_message(~filters.private)
async def catch_taxi_messages(client, message):
    if TARGET_GROUP_ID is not None and message.chat.id == TARGET_GROUP_ID:
        return

    text = message.text or message.caption or ""
    if not text:
        return

    if not is_taxi_request(text):
        return

    if TARGET_GROUP_ID is None:
        print("DEBUG | TARGET_GROUP_ID mavjud emas")
        return

    phone = extract_phone(text)

    # Dublikat xabarni tekshirish (Bir xil xabarni qayta tashlamaslik uchun)
    if is_duplicate(text, phone):
        print(f"⚠️ Dublikat xabar o'tkazib yuborildi: {text[:30]}...")
        return

    try:
        user = message.from_user
        if user:
            first_name = user.first_name or ""
            last_name = user.last_name or ""
            full_name = f"{first_name} {last_name}".strip() or "Mijoz"
            safe_name = html.escape(full_name)

            if user.username:
                user_link = f"<a href='https://t.me/{user.username}'>{safe_name}</a>"
            else:
                user_link = f"<a href='tg://user?id={user.id}'>{safe_name}</a>"
        else:
            user_link = "Noma'lum profil"

        safe_text = html.escape(text)

        if phone:
            phone_fmt = f"<a href='tel:{phone}'>{phone}</a>"
        else:
            phone_fmt = "Ko'rsatilmagan (Profiliga bosing)"

        forward_text = (
            f"👤 <b>Mijoz:</b> {user_link}\n"
            f"📝 <b>Buyurtma:</b> {safe_text}\n\n"
            f"📞 <b>Telefon:</b> {phone_fmt}"
        )

        # 1-usul: Telegram Boti orqali guruhga joylash (Bot tomonidan ko'chirib tashlanishi uchun)
        sent = False
        if bot_sender is not None and TARGET_GROUP_ID is not None:
            try:
                await bot_sender.send_message(
                    chat_id=TARGET_GROUP_ID,
                    text=forward_text,
                    parse_mode="HTML"
                )
                sent = True
                print(f"✅ Xabar Telegram Bot orqali guruhga yuborildi: {text[:30]}...")
            except Exception as b_err:
                print(f"⚠️ Bot orqali yuborishda xatolik: {b_err}, Userbot bilan yuboriladi...")

        # 2-usul: Zaxira tariqasida Userbot orqali yuborish
        if not sent:
            await client.send_message(
                chat_id=TARGET_GROUP_ID,
                text=forward_text,
                parse_mode=enums.ParseMode.HTML
            )
            print(f"✅ Xabar Userbot orqali guruhga yuborildi: {text[:30]}...")

    except Exception as e:
        print(f"❌ Target guruhga xabar yuborishda xatolik: {e}")




async def main():
    await app.start()
    print("Userbot tarmoqqa muvaffaqiyatli ulandi.")

    print("🔄 Dialoglar va guruhlar keshlanmoqda...")
    joined_chats = []
    try:
        async for dialog in app.get_dialogs():
            joined_chats.append(dialog.chat)
        print("✅ Dialoglar muvaffaqiyatli keshlandi.")
    except Exception as exc:
        print(f"⚠️ Dialoglarni keshga yuklashda xatolik: {exc}")

    if TARGET_GROUP_ID is not None:
        try:
            chat = await app.get_chat(TARGET_GROUP_ID)
            print(f"✅ Target guruh aniqlandi: '{chat.title}' (ID: {chat.id})")
        except Exception as exc:
            print(f"⚠️ Target guruh ({TARGET_GROUP_ID}) ga ulanishda xatolik: {exc}")
            print("\n📋 Userbot hozirda a'zo bo'lgan guruhlar ro'yxati:")
            found_target = False
            for c in joined_chats:
                if c.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
                    print(f"  • {c.title} -> ID: {c.id}")
                    if str(c.id) == str(TARGET_GROUP_ID):
                        found_target = True
            if not found_target:
                print(f"⚠️ Eslatma: TARGET_GROUP_ID ({TARGET_GROUP_ID}) ro'yxatda topilmadi.")
                print("Iltimos, userbot ushbu guruhga a'zo ekanligini yoki .env faylidagi ID to'g'riligini tekshiring.")
    else:
        print("⚠️ Ogohlantirish: TARGET_GROUP_ID .env faylida berilmagan.")

    print("\nUserbot ishga tushdi va barcha guruhlardagi xabarlarni tinglamoqda...")
    try:
        await idle()
    finally:
        if bot_sender is not None:
            await bot_sender.session.close()
        await app.stop()


if __name__ == "__main__":
    app.run(main())




