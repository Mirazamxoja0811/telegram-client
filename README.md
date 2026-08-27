# Taxi Client (bot + userbot)

Loyiha 2 ta servisdan iborat:
- `bot.py` — BotFather token bilan ishlaydigan mijoz boti
- `userbot.py` — akkaunt orqali guruhlardan taksi so'rovlarini ushlaydigan userbot

## 1) Sozlash

1. `.env.example` faylni nusxalab `.env` yarating.
2. `.env` ichiga o'zingizning qiymatlarni yozing:
   - `BOT_TOKEN`
   - `GROUP_ID`
   - `API_ID`
   - `API_HASH`
   - `TARGET_GROUP_ID`
   - `USERBOT_SESSION_NAME` (default: `sessions/my_account`)

> Agar `USERBOT_SESSION_STRING` bersangiz, userbot interaktiv login so'ramaydi.

## 2) Docker bilan local ishga tushirish

```bash
docker compose build
docker compose up -d bot
docker compose run --rm userbot
```

`userbot` birinchi ishga tushganda telefon/kod/parol so'raydi va `sessions/` ichida session saqlaydi.
Shundan keyin doimiy rejimda:

```bash
docker compose up -d
```

### `AUTH_KEY_UNREGISTERED` xatosi

Bu xato Telegram serverdagi userbot session kalitini bekor qilganini bildiradi. Bu guruh ID'si yoki bot tokeni xatosi emas. Eski session faylini o'chirib, userbot'ni interaktiv tarzda qayta login qiling:

```bash
docker compose stop userbot
rm -f my_account.session sessions/my_account.session
docker compose run --rm userbot
```

Telefon raqami, Telegram kodi va 2FA parolini kiriting. Login muvaffaqiyatli tugagach, yangi session fayli saqlanadi va servisni qayta ishga tushiring:

```bash
docker compose up -d userbot
docker compose logs -f userbot
```

`USERBOT_SESSION_NAME` `.env` faylida boshqa yo'lga o'rnatilgan bo'lsa, o'chiriladigan `.session` fayli ham shu yo'lda bo'ladi. `USERBOT_SESSION_STRING` ishlatilsa, uning qiymatini yangi login'dan olingan session string bilan almashtiring.

Log ko'rish:

```bash
docker compose logs -f bot
docker compose logs -f userbot
```

## 3) AWS EC2 deploy (Docker)

EC2 Ubuntu instance oching va SSH qiling:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
newgrp docker
```

Repo:

```bash
git clone https://github.com/Mirazamxoja0811/telegram-client.git
cd telegram-client
cp .env.example .env
nano .env
```

Servislarni ishga tushirish:

```bash
docker compose build
docker compose up -d bot
docker compose run --rm userbot
docker compose up -d
```

Auto-restart allaqachon `unless-stopped` bilan yoqilgan.
