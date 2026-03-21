
import telebot
from telebot import types
import json
import os

# 🔑 Bot token
TOKEN = "8627886359:AAEWsjqTz4utPh4UjQFLAVKGRniEOnpTwrk"
bot = telebot.TeleBot(TOKEN)

# 👑 Admin ID
ADMIN_ID = 5633684726

# 📌 Majburiy kanal
REQUIRED_CHANNELS = ["@telefon_reklama_xizmati"]

# 🎬 Kino kanali (ochiq)
KINOBUZA_CHANNEL_ID = -1002671537915  # Kanal ID sini tekshirib o'zgartiring

# 📂 JSON fayllar
MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"

# ⚙ Fayllarni yuklash
if os.path.exists(MOVIES_FILE):
    with open(MOVIES_FILE,"r") as f:
        MOVIES = json.load(f)
else:
    MOVIES = {}

if os.path.exists(USERS_FILE):
    with open(USERS_FILE,"r") as f:
        USERS = json.load(f)
else:
    USERS = []

# 📌 Saqlash funksiyalari
def save_movies():
    with open(MOVIES_FILE,"w") as f:
        json.dump(MOVIES,f)

def save_users():
    with open(USERS_FILE,"w") as f:
        json.dump(USERS,f)

# 🔎 Obunani tekshirish
def check_subscriptions(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch,user_id).status
            if status not in ["member","administrator","creator"]:
                return False
        except:
            return False
    return True

# ✅ /start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id not in USERS:
        USERS.append(message.from_user.id)
        save_users()

    markup = types.InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(
            text=f"Obuna bo'lish {ch}",
            url=f"https://t.me/{ch[1:]}"
        ))
    markup.add(types.InlineKeyboardButton(
        text="✅ Tasdiqlash",
        callback_data="check_subs"
    ))
    bot.send_message(message.chat.id,
                     "Botdan foydalanish uchun kanalga obuna bo‘ling",
                     reply_markup=markup)

# 🔎 Obuna tekshirish tugmasi
@bot.callback_query_handler(func=lambda call: call.data=="check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎬 Kino katalog", "⭐ Top kinolar")
        markup.add("🔎 Kino qidirish")
        if call.from_user.id == ADMIN_ID:
            markup.add("👑 Admin panel")
        bot.send_message(call.message.chat.id,
                         "✅ Obuna tasdiqlandi!\n\nKino kodi yoki nomini kiriting",
                         reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id,
                         "❌ Avval kanalga obuna bo‘ling!")

# 📂 Kino katalogi
@bot.message_handler(func=lambda message: message.text=="🎬 Kino katalog")
def catalog(message):
    text = "🎬 Kino katalog:\n\n"
    for code, info in MOVIES.items():
        text += f"Kino kodi: {code} - {info['name']}\n"
    bot.send_message(message.chat.id, text)

# 🔎 Kino nomi bilan qidirish
@bot.message_handler(func=lambda message: message.text.startswith("🔎"))
def search(message):
    query = message.text[1:].strip().lower()
    results = ""
    for code, info in MOVIES.items():
        if query in info['name'].lower():
            results += f"{info['name']} - Kod: {code}\n"
    if results:
        bot.send_message(message.chat.id, results)
    else:
        bot.send_message(message.chat.id, "❌ Hech narsa topilmadi")

# 🎥 Kino kodi bilan yuborish
@bot.message_handler(func=lambda message: message.text.isdigit())
def send_movie(message):
    if not check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id,"❌ Avval kanalga obuna bo‘ling")
        return

    code = message.text
    if code in MOVIES:
        post_id = MOVIES[code]['post']
        bot.forward_message(message.chat.id, KINOBUZA_CHANNEL_ID, post_id)
    else:
        bot.send_message(message.chat.id, "❌ Bunday kino kodi yo‘q")

# 👑 Admin panel
@bot.message_handler(func=lambda message: message.text=="👑 Admin panel")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Kino qo‘shish", "❌ Kino o‘chirish")
    markup.add("📊 Statistika", "📢 Reklama yuborish")
    bot.send_message(message.chat.id, "👑 Admin panel", reply_markup=markup)

# ➕ Kino qo‘shish
@bot.message_handler(func=lambda message: message.text=="➕ Kino qo‘shish")
def add_movie_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "Kanal postini forward qilib yuboring, bot avtomatik kino kodini beradi")

    @bot.message_handler(func=lambda m: m.forward_from_chat and m.from_user.id==ADMIN_ID, content_types=['video','document','photo'])
    def forward_add(m):
        next_code = str(max([int(c) for c in MOVIES.keys()] + [0]) + 1)
        MOVIES[next_code] = {"post": m.forward_from_message_id, "name": m.caption or f"Kino {next_code}"}
        save_movies()
        bot.send_message(m.chat.id, f"✅ Kino qo‘shildi! Kodi: {next_code}")

# ❌ Kino o‘chirish
@bot.message_handler(func=lambda message: message.text=="❌ Kino o‘chirish")
def delete_movie_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "❌ Kino o‘chirish uchun kodni kiriting")

    @bot.message_handler(func=lambda m: m.from_user.id==ADMIN_ID)
    def delete_code(m):
        code = m.text.strip()
        if code in MOVIES:
            del MOVIES[code]
            save_movies()
            bot.send_message(m.chat.id, f"✅ Kino {code} o‘chirildi")
        else:
            bot.send_message(m.chat.id, "❌ Bunday kod mavjud emas")

# 📊 Statistika
@bot.message_handler(func=lambda message: message.text=="📊 Statistika")
def stat(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, f"👥 Foydalanuvchilar soni: {len(USERS)}")

# 📢 Rasm / video bilan reklama
@bot.message_handler(func=lambda message: message.text=="📢 Reklama yuborish")
def broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "Reklama yuborish uchun postga reply qilib /send yozing")

@bot.message_handler(commands=['send'])
def send_ad(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❌ Reply qilgan post kerak")
        return
    msg = message.reply_to_message
    for user in USERS:
        try:
            bot.copy_message(user, message.chat.id, msg.message_id)
        except:
            pass
    bot.send_message(message.chat.id, "✅ Reklama yuborildi")

# ⭐ Top kinolar (eng ko‘p so‘ralgan)
# Bu uchun siz qo‘shimcha "views" counter qo‘shishingiz mumkin
# Hozircha kodi forward qilinsa hisoblamaydi, keyin qo‘shimcha qilish mumkin

print("🤖 Bot ishga tushdi...")
bot.infinity_polling()