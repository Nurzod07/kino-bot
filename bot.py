import telebot
from telebot import types
import json
import os

TOKEN = "8627886359:AAEWsjqTz4utPh4UjQFLAVKGRniEOnpTwrk"
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 5633684726
REQUIRED_CHANNELS = ["@telefon_reklama_xizmati"]
KINOBUZA_CHANNEL_ID = -1002671537915

MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"

# Fayllarni yuklash
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

def check_subscriptions(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ["member","administrator","creator"]:
                return False
        except:
            return False
    return True

# START
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

# CHECK SUB
@bot.callback_query_handler(func=lambda call: call.data=="check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("🎬 Kino katalog", "⭐ Top kinolar")
        markup.add("🔎 Kino qidirish")
        if call.from_user.id == ADMIN_ID:
            markup.add("👑 Admin panel")

        bot.send_message(call.message.chat.id,
                         "✅ Obuna tasdiqlandi!\n\nKino kodi yoki nomini yozing",
                         reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id,
                         "❌ Avval kanalga obuna bo‘ling!")

# KATALOG
@bot.message_handler(func=lambda message: message.text=="🎬 Kino katalog")
def catalog(message):
    text = "🎬 Kino katalog:\n\n"
    for code, info in MOVIES.items():
        text += f"{code} - {info['name']}\n"
    bot.send_message(message.chat.id, text)

# QIDIRISH
@bot.message_handler(func=lambda message: message.text.startswith("🔎"))
def search(message):
    query = message.text[1:].strip().lower()
    result = ""
    for code, info in MOVIES.items():
        if query in info['name'].lower():
            result += f"{info['name']} - {code}\n"

    if result:
        bot.send_message(message.chat.id, result)
    else:
        bot.send_message(message.chat.id, "❌ Topilmadi")

# KINO YUBORISH
@bot.message_handler(func=lambda message: message.text.isdigit())
def send_movie(message):
    if not check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id,"❌ Avval obuna bo‘ling")
        return

    code = message.text

    if code in MOVIES:
        bot.forward_message(message.chat.id,
                            KINOBUZA_CHANNEL_ID,
                            MOVIES[code]["post"])
    else:
        bot.send_message(message.chat.id,"❌ Bunday kod yo‘q")

# ADMIN PANEL
@bot.message_handler(func=lambda message: message.text=="👑 Admin panel")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Kino qo‘shish", "❌ Kino o‘chirish")
    markup.add("📊 Statistika", "📢 Reklama")

    bot.send_message(message.chat.id, "👑 Admin panel", reply_markup=markup)

# ⭐ FIX QILINDI KINO QO‘SHISH
ADD_STATE = {}

@bot.message_handler(func=lambda message: message.text=="➕ Kino qo‘shish")
def add_movie(message):
    if message.from_user.id != ADMIN_ID:
        return

    ADD_STATE[message.from_user.id] = True
    bot.send_message(message.chat.id, "📥 Kanal postini forward qiling")

@bot.message_handler(content_types=['video','document','photo'])
def get_movie(message):

    if message.from_user.id != ADMIN_ID:
        return

    if message.from_user.id not in ADD_STATE:
        return

    if not message.forward_from_chat:
        bot.send_message(message.chat.id,"❌ Forward qiling")
        return

    code = str(max([int(x) for x in MOVIES.keys()] + [0]) + 1)

    MOVIES[code] = {
        "post": message.forward_from_message_id,
        "name": message.caption or f"Kino {code}"
    }

    save_movies()

    del ADD_STATE[message.from_user.id]

    bot.send_message(message.chat.id,f"✅ Qo‘shildi\nKod: {code}")

# O‘CHIRISH
@bot.message_handler(func=lambda message: message.text=="❌ Kino o‘chirish")
def delete_movie(message):
    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(message.chat.id,"Kod yubor")

    @bot.message_handler(func=lambda m: m.from_user.id==ADMIN_ID)
    def delete(m):
        if m.text in MOVIES:
            del MOVIES[m.text]
            save_movies()
            bot.send_message(m.chat.id,"✅ O‘chirildi")
        else:
            bot.send_message(m.chat.id,"❌ Topilmadi")

# STAT
@bot.message_handler(func=lambda message: message.text=="📊 Statistika")
def stat(message):
    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(message.chat.id,f"👥 {len(USERS)} ta foydalanuvchi")

# REKLAMA
@bot.message_handler(func=lambda message: message.text=="📢 Reklama")
def reklama(message):
    if message.from_user.id != ADMIN_ID:
        return

    bot.send_message(message.chat.id,"Reply + /send")

@bot.message_handler(commands=['send'])
def send_ad(message):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.reply_to_message:
        return

    for user in USERS:
        try:
            bot.copy_message(user,
                             message.chat.id,
                             message.reply_to_message.message_id)
        except:
            pass

    bot.send_message(message.chat.id,"✅ Yuborildi")

print("🤖 Bot ishlayapti...")
bot.infinity_polling()