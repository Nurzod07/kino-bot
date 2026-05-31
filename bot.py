import telebot
from telebot import types
import sqlite3
import os
import time
from flask import Flask
from threading import Thread

# --- VEB SERVER (RENDER UCHUN) ---
app = Flask('')
@app.route('/')
def home(): return "Bot faol!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- SOZLAMALAR ---
TOKEN = "TOKEN_SHU_YERGA" # ⚠️ BotFather bergan tokenni kiriting!
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5633684726 # ⚠️ Sizning ID raqamingiz

REQUIRED_CHANNELS = ["@telefon_reklama_xizmati", "@piimaenglish_edu", "@piima_kitab", "@ogirlangansamo"]
INSTAGRAM_URL = "https://www.instagram.com/yangi__tv?igsh=ZTI3YmR5MXVoemU5"

# --- MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (code TEXT PRIMARY KEY, file_id TEXT, content_type TEXT, caption TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, join_date TEXT)''')
    conn.commit()
    conn.close()

def add_user_to_db(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, ?)", (user_id, time.strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

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
    try:
        cursor.execute("SELECT code FROM movies ORDER BY CAST(code AS INTEGER) DESC LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        if result: return int(result[0])
    except:
        conn.close()
    return 0

def check_subscriptions(user_id):
    if user_id == ADMIN_ID: return True
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

def get_subscription_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, ch in enumerate(REQUIRED_CHANNELS, 1):
        markup.add(types.InlineKeyboardButton(text=f"📢 {i}-kanalga obuna bo'lish", url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton(text="📸 Instagram sahifamiz", url=INSTAGRAM_URL))
    markup.add(types.InlineKeyboardButton(text="✅ Obunani tasdiqlash", callback_data="check_subs"))
    return markup

def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if user_id == ADMIN_ID:
        markup.add("🔍 Kino qidirish", "📊 Statistika")
        markup.add("👑 Admin Panel")
    else:
        markup.add("🔍 Kino qidirish", "✍️ Biz bilan aloqa")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    add_user_to_db(message.from_user.id)
    if check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id, "👋 Xush kelibsiz! Kino kodini yuboring:", reply_markup=get_main_keyboard(message.from_user.id))
    else:
        bot.send_message(message.chat.id, "⚠️ Botdan foydalanish uchun kanallarga a'zo bo'ling:", reply_markup=get_subscription_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "✅ Tasdiqlandi! Kino kodini yuboring:", reply_markup=get_main_keyboard(call.from_user.id))
    else:
        bot.answer_callback_query(call.id, "❌ Kanallarga obuna bo'ling!", show_alert=True)

# 🚀 AVTOMATIK KINO QO'SHISH TIZIMI (ADMIN SENZURASI)
@bot.message_handler(content_types=['video', 'document', 'audio'])
def auto_add_movie(message):
    # Agar oddiy odam video tashlasa, bot qabul qilmaydi
    if message.from_user.id != ADMIN_ID:
        if not check_subscriptions(message.from_user.id):
            bot.send_message(message.chat.id, "❌ Avval kanallarga obuna bo'ling!", reply_markup=get_subscription_keyboard())
        return

    # Agar admin video, fayl yoki audio yuborsa/forward qilsa - AVTOMATIK BAZAGA QO'SHADI
    file_id = None
    content_type = None
    caption = message.caption if message.caption else "Nomsiz kino"

    if message.video:
        file_id = message.video.file_id
        content_type = 'video'
    elif message.document:
        file_id = message.document.file_id
        content_type = 'document'
    elif message.audio:
        file_id = message.audio.file_id
        content_type = 'audio'

    if file_id:
        try:
            conn = sqlite3.connect('bot_data.db')
            cursor = conn.cursor()
            last_code = get_last_movie_code()
            new_code = str(last_code + 1)
            cursor.execute("INSERT OR REPLACE INTO movies (code, file_id, content_type, caption) VALUES (?, ?, ?, ?)", 
                           (new_code, file_id, content_type, caption))
            conn.commit()
            conn.close()
            bot.send_message(message.chat.id, f"✅ Kino bazaga muvaffaqiyatli saqlandi!\n\n🎬 Kino kodi: `{new_code}`\n🎥 Nomi: {caption}", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Bazaga saqlashda xato yuz berdi: {e}")

# --- MATNLAR BILAN ISHLASH ---
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    if not check_subscriptions(message.from_user.id): return

    text = message.text
    
    # Kod bo'yicha kino qidirish
    if text.isdigit():
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT file_id, content_type, caption FROM movies WHERE code=?", (text,))
        movie_data = cursor.fetchone()
        conn.close()

        if movie_data:
            file_id, c_type, caption = movie_data
            try:
                if c_type == 'video': 
                    bot.send_video(message.chat.id, file_id, caption=f"🎬 Kod: {text}\n🎥 Nomi: {caption}")
                elif c_type == 'document':
                    bot.send_document(message.chat.id, file_id, caption=f"🎬 Kod: {text}\n🎥 Nomi: {caption}")
                elif c_type == 'audio':
                    bot.send_audio(message.chat.id, file_id, caption=f"🎬 Kod: {text}\n🎥 Nomi: {caption}")
            except: 
                bot.send_message(message.chat.id, "❌ Fayl serverdan o'chirilgan yoki xatolik.")
        else:
            bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")
        return

    # Admin amallari
    if text == "📊 Statistika" and message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"📊 BOT STATISTIKASI:\n\n👥 Foydalanuvchilar: {get_users_count()} ta\n🎬 Kinolar: {get_movies_count()} ta")

    elif text == "👑 Admin Panel" and message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📢 Reklama Tarqatish", "🔙 Orqaga")
        bot.send_message(message.chat.id, "👑 Admin Panel:", reply_markup=markup)

    elif text == "📢 Reklama Tarqatish" and message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "📢 Reklama postini yuboring:")
        bot.register_next_step_handler(msg, send_reklama)
        
    elif text == "🔙 Orqaga":
        bot.send_message(message.chat.id, "Menyu:", reply_markup=get_main_keyboard(message.from_user.id))

def send_reklama(message):
    users = get_all_users()
    for u_id in users:
        try: bot.copy_message(chat_id=u_id, from_chat_id=message.chat.id, message_id=message.message_id)
        except: pass
    bot.send_message(message.chat.id, "✅ Reklama tarqatildi!", reply_markup=get_main_keyboard(ADMIN_ID))

if __name__ == "__main__":
    init_db()
    keep_alive()
    bot.infinity_polling()
