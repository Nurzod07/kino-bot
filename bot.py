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
TOKEN = "8627886359:AAEWsjqTz4utPh4UjQFLAVKGRniEOnpTwrk"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5633684726

REQUIRED_CHANNELS = ["@telefon_reklama_xizmati", "@piimaenglish_edu","@piima_kitab","@ogirlangansamo"]
INSTAGRAM_URL = "https://www.instagram.com/yangi__tv?igsh=ZTI3YmR5MXVoemU5"

# --- BAZA BILAN ISHLASH (file_id qo'shildi) ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    # file_id va content_type ustunlari qo'shildi
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (code TEXT PRIMARY KEY, file_id TEXT, content_type TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

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
    return result # (file_id, content_type) qaytaradi

# --- QOLGAN FUNKSIYALAR ---

@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❗ Kinoga (video/fayl) reply qilib /add yozing")
        return

    msg = message.reply_to_message
    file_id = None
    content_type = None

    # Fayl turini aniqlash
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
            new_code = str(int(last_code) + 1)
            add_movie_to_db(new_code, file_id, content_type)
            bot.send_message(message.chat.id, f"✅ Baza saqlandi!\n🎬 Kino kodi: {new_code}\nℹ️ Endi bu faylni o'chirib yuborsangiz ham bot ishlayveradi.")
        except Exception as e:
            bot.send_message(message.chat.id, f"Xato: {e}")
    else:
        bot.send_message(message.chat.id, "❗ Bu xabar turini saqlab bo'lmaydi (Faqat video yoki fayl yuboring).")

@bot.message_handler(func=lambda message: message.text.isdigit())
def send_movie(message):
    if not check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Avval kanallarga obuna bo'ling!")
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
            bot.send_message(message.chat.id, "❌ Xato: Fayl Telegram serveridan o'chib ketgan.")
    else:
        bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")

# --- Boshqa funksiyalar (start, check, reklama, stat) o'zgarishsiz qoladi ---
