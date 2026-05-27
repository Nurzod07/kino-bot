import telebot
from telebot import types
import sqlite3
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

# --- SOZLAMALAR ---
# ⚠️ DIQQAT: Bu yerga BotFather bergan YANGI TOKENNI qo'ying!
TOKEN = "8627886359:AAG4FHpR5tVq3PqL9SnJbJL9fNjaSk78Bcg" 
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5633684726

REQUIRED_CHANNELS = ["@telefon_reklama_xizmati", "@piimaenglish_edu", "@piima_kitab", "@ogirlangansamo"]
INSTAGRAM_URL = "https://www.instagram.com/yangi__tv?igsh=ZTI3YmR5MXVoemU5"

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (code TEXT PRIMARY KEY, file_id TEXT, content_type TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def add_user_to_db(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_users_count():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_movies_count():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_last_movie_code():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM movies CAST(code AS INTEGER)")
    results = cursor.fetchall()
    conn.close()
    if results:
        codes = [int(r[0]) for r in results if r[0].isdigit()]
        return max(codes) if codes else 0
    return 0

def add_movie_to_db(code, file_id, content_type):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO movies (code, file_id, content_type) VALUES (?, ?, ?)", 
                   (code, file_id, content_type))
    conn.commit()
    conn.close()

def get_movie_from_db(code):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, content_type FROM movies WHERE code=?", (code,))
    result = cursor.fetchone()
    conn.close()
    return result

# --- OBUNA TEKSHIRUV ---
def check_subscriptions(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# --- KOMANDALAR ---
@bot.message_handler(commands=['start'])
def start(message):
    add_user_to_db(message.from_user.id)
    
    markup = types.InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(text=f"📢 {ch}", url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton(text="📸 Instagram", url=INSTAGRAM_URL))
    markup.add(types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_subs"))

    bot.send_message(
        message.chat.id,
        "📢 Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling va Tasdiqlash tugmasini bosing:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Rahmat! Obuna tasdiqlandi. Endi kino kodini yuborishingiz mumkin. 👇")
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❗ Kinoga (video/fayl) reply qilib /add yozing")
        return

    msg = message.reply_to_message
    file_id = None
    content_type = None

    if msg.video:
        file_id = msg.video.file_id
        content_type = 'video'
    elif msg.document:
        file_id = msg.document.file_id
        content_type = 'document'
    elif msg.audio:
        file_id = msg.audio.file_id
        content_type = 'audio'

    if file_id:
        try:
            last_code = get_last_movie_code()
            new_code = str(last_code + 1)
            add_movie_to_db(new_code, file_id, content_type)
            bot.send_message(message.chat.id, f"✅ Baza saqlandi!\n🎬 Kino kodi: {new_code}")
        except Exception as e:
            bot.send_message(message.chat.id, f"Xato: {e}")
    else:
        bot.send_message(message.chat.id, "❗ Faqat video, audio yoki hujjat (fayl) turidagi xabarlarni saqlash mumkin.")

@bot.message_handler(func=lambda message: message.text.isdigit())
def send_movie(message):
    if not check_subscriptions(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        for ch in REQUIRED_CHANNELS:
            markup.add(types.InlineKeyboardButton(text=f"📢 {ch}", url=f"https://t.me/{ch[1:]}"))
        markup.add(types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_subs"))
        bot.send_message(message.chat.id, "❌ Botdan foydalanish uchun kanallarga obuna bo'ling!", reply_markup=markup)
        return

    code = message.text
    movie_data = get_movie_from_db(code)

    if movie_data:
        file_id, c_type = movie_data
        try:
            if c_type == 'video':
                bot.send_video(message.chat.id, file_id)
            elif c_type == 'document':
                bot.send_document(message.chat.id, file_id)
            elif c_type == 'audio':
                bot.send_audio(message.chat.id, file_id)
        except Exception as e:
            bot.send_message(message.chat.id, "❌ Xato: Fayl Telegram serveridan o'chib ketgan yoki bot uni yubora olmayapti.")
    else:
        bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")

@bot.message_handler(commands=['stat'])
def stat(message):
    if message.from_user.id != ADMIN_ID: return
    u_count = get_users_count()
    m_count = get_movies_count()
    bot.send_message(message.chat.id, f"📊 Bot statistikasi:\n\n👥 Foydalanuvchilar: {u_count} ta\n🎬 Kinolar bazasi: {m_count} ta")

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    init_db()
    print("🤖 Bot ishga tushdi...")
    keep_alive()
    bot.infinity_polling()
