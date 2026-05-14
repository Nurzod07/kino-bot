import telebot
from telebot import types
import sqlite3
import os
from flask import Flask
from threading import Thread

# --- VEB SERVER (Render uchun) ---
app = Flask('')
@app.route('/')
def home(): return "Bot ishlanyapti!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- SOZLAMALAR ---
TOKEN = "8627886359:AAEWsjqTz4utPh4UjQFLAVKGRniEOnpTwrk"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5633684726

# Majburiy obuna kanallari
REQUIRED_CHANNELS = ["@telefon_reklama_xizmati", "@piimaenglish_edu","@piima_kitab","@ogirlangansamo"]
# Instagram manzili
INSTAGRAM_URL = "https://www.instagram.com/yangi__tv?igsh=ZTI3YmR5MXVoemU5"

# --- BAZA BILAN ISHLASH (SQLite) ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies (code TEXT PRIMARY KEY, message_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

def add_user_to_db(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def add_movie_to_db(code, msg_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO movies (code, message_id) VALUES (?, ?)", (code, msg_id))
    conn.commit()
    conn.close()

def get_movie_from_db(code):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM movies WHERE code=?", (code,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_last_movie_code():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(CAST(code AS INTEGER)) FROM movies")
    result = cursor.fetchone()[0]
    conn.close()
    return result if result else 0

# --- BOT FUNKSIYALARI ---

def check_subscriptions(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

@bot.message_handler(commands=['start'])
def start(message):
    add_user_to_db(message.from_user.id)
    
    markup = types.InlineKeyboardMarkup()
    # Telegram kanallar
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(text=f"📢 Obuna bo'lish", url=f"https://t.me/{ch[1:]}"))
    
    # Instagram tugmasi (Tekshirilmaydi, shunchaki ko'rinadi)
    markup.add(types.InlineKeyboardButton(text="📸 Instagram (Obuna bo'ling)", url=INSTAGRAM_URL))
    
    # Tasdiqlash
    markup.add(types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_subs"))

    bot.send_message(message.chat.id, "🎬 Botdan foydalanish uchun quyidagi sahifalarga obuna bo'ling:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data=="check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        bot.send_message(call.message.chat.id, "✅ Xush kelibsiz! Kino kodini yuboring.")
    else:
        bot.answer_callback_query(call.id, "❌ Hali hamma kanallarga obuna bo'lmagansiz!", show_alert=True)

# ➕ KINO QO'SHISH
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❗ Kinoga reply qilib /add yozing")
        return

    msg = message.reply_to_message
    try:
        last_code = get_last_movie_code()
        new_code = str(last_code + 1)
        add_movie_to_db(new_code, msg.message_id)
        bot.send_message(message.chat.id, f"✅ Qo'shildi!\n🎬 Kino kodi: {new_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xato: {e}")

# 🚀 REKLAMA YUBORISH
@bot.message_handler(commands=['reklama'])
def send_reklama(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❗ Reklama xabarini ustiga reply qilib /reklama deb yozing.")
        return

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    all_users = cursor.fetchall()
    conn.close()

    count = 0
    error_count = 0
    status_msg = bot.send_message(message.chat.id, "🚀 Tarqatish boshlandi...")

    for user in all_users:
        try:
            bot.copy_message(chat_id=user[0], from_chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
            count += 1
        except:
            error_count += 1
            continue

    bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, 
                          text=f"✅ Tugadi!\n👤 Qabul qildi: {count}\n❌ Bloklagan: {error_count}")

# 🎬 KINO YUBORISH
@bot.message_handler(func=lambda message: message.text.isdigit())
def send_movie(message):
    if not check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Avval kanallarga obuna bo'ling!")
        return

    code = message.text
    msg_id = get_movie_from_db(code)
    
    if msg_id:
        try:
            bot.copy_message(chat_id=message.chat.id, from_chat_id=ADMIN_ID, message_id=msg_id)
        except:
            bot.send_message(message.chat.id, "❌ Xato: Kino topilmadi yoki o'chirilgan.")
    else:
        bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")

# 📊 STATISTIKA
@bot.message_handler(commands=['stat'])
def stat(message):
    if message.from_user.id == ADMIN_ID:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        u_count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        m_count = cursor.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
        conn.close()
        bot.send_message(message.chat.id, f"📊 Statistika:\n👥 Foydalanuvchilar: {u_count}\n🎬 Kinolar: {m_count}")

if __name__ == "__main__":
    init_db()
    keep_alive()
    bot.infinity_polling()
