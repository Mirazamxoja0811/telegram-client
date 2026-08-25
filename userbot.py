from pyrogram import Client, filters
import asyncio
import re
import os
from dotenv import load_dotenv

load_dotenv()

api_id_raw = os.getenv("API_ID", "").strip()
if not api_id_raw:
    raise RuntimeError("API_ID topilmadi. .env faylga API_ID kiriting.")
try:
    API_ID = int(api_id_raw)
except ValueError as err:
    raise RuntimeError("API_ID butun son bo'lishi kerak.") from err

API_HASH = os.getenv("API_HASH", "").strip()
if not API_HASH:
    raise RuntimeError("API_HASH topilmadi. .env faylga API_HASH kiriting.")

target_group_id_raw = os.getenv("TARGET_GROUP_ID", "").strip()
if not target_group_id_raw:
    raise RuntimeError("TARGET_GROUP_ID topilmadi. .env faylga TARGET_GROUP_ID kiriting.")
try:
    TARGET_GROUP_ID = int(target_group_id_raw)
except ValueError as err:
    raise RuntimeError("TARGET_GROUP_ID butun son bo'lishi kerak.") from err

session_name = os.getenv("USERBOT_SESSION_NAME", "my_account").strip() or "my_account"
app = Client(session_name, api_id=API_ID, api_hash=API_HASH)

# Kalit so'zlar
CITIES = ["toshkent", "vodiy", "andijon", "farg'ona", "fargona", "namangan", "qo'qon", "marg'ilon", "tashkent"]
KEYWORDS = ["kishi", "odam", "bor", "pochta", "ketyapman", "beraman", "ming", "som", "so'm"]

def is_taxi_request(text: str) -> bool:
    if not text:
        return False
    text = text.lower()
    
    # Matn ichida hech bo'lmaganda 1 ta shahar nomi...
    has_city = any(city in text for city in CITIES)
    # va 1 ta taksiga oid so'z qatnashganligini tekshirish
    has_keyword = any(keyword in text for keyword in KEYWORDS)
    
    return has_city and has_keyword

@app.on_message(filters.group & filters.text)
async def catch_taxi_messages(client, message):
    # O'z guruhimizdagi xabarlarga e'tibor bermaymiz
    if message.chat.id == TARGET_GROUP_ID:
        return

    if is_taxi_request(message.text):
        try:
            # Xabarni haydovchilar guruhiga forward qilamiz (agar ruxsat bo'lsa)
            # yoki matnidan nusxa olib, profil linkini qo'shib yuboramiz.
            
            user_id = message.from_user.id if message.from_user else None
            user_name = message.from_user.first_name if message.from_user else "Noma'lum"
            chat_name = message.chat.title
            
            forward_text = f"🚨 <b>Yangi mijoz ushlandi!</b>\n" \
                           f"📍 Guruh: {chat_name}\n" \
                           f"👤 Mijoz: <a href='tg://user?id={user_id}'>{user_name}</a>\n\n" \
                           f"💬 Xabar: <i>{message.text}</i>"
                           
            await client.send_message(
                chat_id=TARGET_GROUP_ID,
                text=forward_text,
                parse_mode=None # pyrogram default is HTML format for tags
            )
            print(f"Xabar ushlandi va yuborildi: {message.text[:20]}...")
            
        except Exception as e:
            print(f"Xatolik: {e}")

if __name__ == "__main__":
    print("Userbot ishga tushmoqda...")
    app.run()
