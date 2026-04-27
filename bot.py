import telebot
from telebot import types
import json
import os
from flask import Flask
from threading import Thread

# --- VEB SERVER (RENDER UCHUN) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot ishlanyapti!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --------------------------------

TOKEN = "8627886359:AAEWsjqTz4utPh4UjQFLAVKGRniEOnpTwrk"
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 5633684726

REQUIRED_CHANNELS = [
    "@telefon_reklama_xizmati",
    "@piimaenglish_edu"
]

KINOBUZA_CHANNEL_ID = -1002671537915

MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"

# 📂 Fayllar yuklash
if os.path.exists(MOVIES_FILE):
    with open(MOVIES_FILE, "r") as f:
        MOVIES = json.load(f)
else:
    MOVIES = {}

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        USERS = json.load(f)
else:
    USERS = []

def save_movies():
    with open(MOVIES_FILE, "w") as f:
        json.dump(MOVIES, f)

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(USERS, f)

# 🔎 Obuna tekshiruv
def check_subscriptions(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ▶️ START
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id not in USERS:
        USERS.append(message.from_user.id)
        save_users()

    markup = types.InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(
            text=f"📢 {ch}",
            url=f"https://t.me/{ch[1:]}"
        ))

    markup.add(types.InlineKeyboardButton(
        text="✅ Tasdiqlash",
        callback_data="check_subs"
    ))

    bot.send_message(
        message.chat.id,
        "📢 Botdan foydalanish uchun kanallarga obuna bo‘ling:",
        reply_markup=markup
    )

# ✅ TASDIQLASH
@bot.callback_query_handler(func=lambda call: call.data=="check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎬 Kino katalog")
        if call.from_user.id == ADMIN_ID:
            markup.add("👑 Admin panel")

        bot.send_message(
            call.message.chat.id,
            "✅ Tasdiqlandi!\n\n🎬 Kino kodini yuboring",
            reply_markup=markup
        )
    else:
        bot.answer_callback_query(call.id, "❌ Avval obuna bo‘ling!", show_alert=True)

# 🎬 KINO YUBORISH
@bot.message_handler(func=lambda message: message.text.isdigit())
def send_movie(message):
    if not check_subscriptions(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        for ch in REQUIRED_CHANNELS:
            markup.add(types.InlineKeyboardButton(text=f"📢 {ch}", url=f"https://t.me/{ch[1:]}"))
        markup.add(types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_subs"))
        bot.send_message(message.chat.id, "❌ Avval kanallarga obuna bo‘ling!", reply_markup=markup)
        return

    code = message.text
    if code in MOVIES:
        bot.copy_message(message.chat.id, KINOBUZA_CHANNEL_ID, MOVIES[code])
    else:
        bot.send_message(message.chat.id, "❌ Bunday kod yo‘q")

# ➕ KINO QO‘SHISH
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❗ Postga reply qilib /add yozing")
        return

    msg = message.reply_to_message
    try:
        code = str(max([int(x) for x in MOVIES.keys()] + [0]) + 1)
        # Forward_from_message_id faqat kanaldan forward qilinganda ishlaydi
        MOVIES[code] = msg.message_id 
        save_movies()
        bot.send_message(message.chat.id, f"✅ Qo‘shildi\nKod: {code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xato: {e}")

# 📊 STATISTIKA
@bot.message_handler(commands=['stat'])
def stat(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, f"📊 STATISTIKA\n\n👥 Foydalanuvchilar: {len(USERS)} ta\n🎬 Kinolar: {len(MOVIES)} ta")

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    print("🤖 Bot ishlayapti...")
    keep_alive()  # Veb serverni alohida oqimda yoqish
    bot.infinity_polling()
