import telebot
from telebot import types
import json
import os
from flask import Flask
from threading import Thread

# --- VEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot ishlanyapti!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = "8627886359:AAEWsjqTz4utPh4UjQFLAVKGRniEOnpTwrk"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5633684726

# Kanallar ro'yxati
REQUIRED_CHANNELS = ["@telefon_reklama_xizmati", "@piimaenglish_edu"]

MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"

# Fayllarni yuklash
if os.path.exists(MOVIES_FILE):
    with open(MOVIES_FILE, "r") as f: MOVIES = json.load(f)
else: MOVIES = {}

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f: USERS = json.load(f)
else: USERS = []

def save_movies():
    with open(MOVIES_FILE, "w") as f: json.dump(MOVIES, f)

def save_users():
    with open(USERS_FILE, "w") as f: json.dump(USERS, f)

def check_subscriptions(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id not in USERS:
        USERS.append(message.from_user.id)
        save_users()
    
    markup = types.InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(text=f"📢 Obuna bo'lish", url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_subs"))
    
    bot.send_message(message.chat.id, "🎬 Botdan foydalanish uchun kanallarga obuna bo'ling:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data=="check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        bot.send_message(call.message.chat.id, "✅ Xush kelibsiz! Kino kodini yuboring.")
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmagansiz!", show_alert=True)

# ➕ KINO QO'SHISH (YANGI VA ISHONCHLI USUL)
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❗ Kinoga reply qilib /add yozing")
        return

    msg = message.reply_to_message
    try:
        # Yangi kod yaratish
        new_code = str(max([int(x) for x in MOVIES.keys()] + [0]) + 1)
        # BU YERDA XABARNING BOT CHATIDAGI ID SINI SAQLAYMIZ
        MOVIES[new_code] = msg.message_id
        save_movies()
        bot.send_message(message.chat.id, f"✅ Qo'shildi!\n🎬 Kino kodi: {new_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xato: {e}")

# 🎬 KINO YUBORISH
@bot.message_handler(func=lambda message: message.text.isdigit())
def send_movie(message):
    if not check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Avval kanallarga obuna bo'ling!")
        return

    code = message.text
    if code in MOVIES:
        try:
            # BOT KINONI O'ZIDAN (ADMIN BILAN BO'LGAN CHATDAN) NUSXALAB BERADI
            bot.copy_message(chat_id=message.chat.id, from_chat_id=ADMIN_ID, message_id=MOVIES[code])
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Kinoni yuborishda xato. Admin kinoni botdan o'chirib yuborgan bo'lishi mumkin.")
    else:
        bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")

@bot.message_handler(commands=['stat'])
def stat(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"📊 Statistika:\n👥 Foydalanuvchilar: {len(USERS)}\n🎬 Kinolar: {len(MOVIES)}")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()