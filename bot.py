import telebot
from telebot import types
import sqlite3
import os
import time
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
TOKEN = "TOKEN_SHU_YERGA" 
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
        if result and result[0].isdigit():
            return int(result[0])
    except Exception as e:
        print(f"Baza o'qishda xato: {e}")
        conn.close()
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
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
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

# --- REKLAMA FUNKSIYASI (YANGI) ---
@bot.message_handler(commands=['send_reklama'])
def start_reklama(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.send_message(message.chat.id, "📢 Reklama xabarini yuboring (Matn, rasm, video yoki forward xabar bo'lishi mumkin):")
    bot.register_next_step_handler(msg, send_reklama_to_all)

def send_reklama_to_all(message):
    users = get_all_users()
    succes = 0
    failed = 0
    
    status_msg = bot.send_message(message.chat.id, f"⏳ Reklama yuborish boshlandi (Jami: {len(users)} ta foydalanuvchi)...")
    
    for u_id in users:
        try:
            # Xabarni qanday bo'lsa shundayligicha forward (uzatish) qiladi
            bot.forward_message(u_id, message.chat.id, message.message_id)
            succes += 1
            time.sleep(0.05) # Telegram bloklab qo'ymasligi uchun kichik pauza
        except:
            failed += 1
            
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        text=f"✅ Reklama yakunlandi!\n\nYuborildi: {succes} ta foydalanuvchiga\nO'chib ketgan/Bloklagan: {failed} ta"
    )

@bot.message_handler(commands=['stat'])
def stat(message):
    if message.from_user.id != ADMIN_ID: return
    u_count = get_users_count()
    m_count = get_movies_count()
    bot.send_message(message.chat.id, f"📊 Bot statistikasi:\n\n👥 Foydalanuvchilar: {u_count} ta\n🎬 Kinolar bazasi: {m_count} ta\n\n📢 Reklama yuborish uchun: /send_reklama")

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

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    init_db()
    print("🤖 Bot ishga tushdi...")
    keep_alive()
    bot.infinity_polling()
