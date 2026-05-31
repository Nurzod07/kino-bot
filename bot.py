import telebot
from telebot import types
import sqlite3
import os
import time
from flask import Flask
from threading import Thread

# --- VEB SERVER (RENDER 24/7 UCHUN) ---
app = Flask('')
@app.route('/')
def home(): return "Bot faol va onlayn!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ASOSIY SOZLAMALAR ---
import os
TOKEN = os.environ.get("BOT_TOKEN") # 👈 Tokenni kod ichiga yozmaymiz, Render'dan oladi!
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5633684726  # ⚠️ Sizning ID raqamingiz

# Kanallar ro'yxati
REQUIRED_CHANNELS = ["@telefon_reklama_xizmati", "@piima_kitab", "@piimaenglish_edu", "@ogirlangansamo"]
INSTAGRAM_URL = "https://www.instagram.com/yangi__tv?igsh=ZTI3YmR5MXVoemU5"
REKLAMA_KANAL_URL = "https://t.me/Arzon_reklama07"

# --- MA'LUMOTLAR BAZASI AMALLARI ---
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

# --- OBUNA TEKSHIRISH ---
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

# --- KLAVIATURALAR (TUGMALAR) ---
def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if user_id == ADMIN_ID:
        markup.add("🔍 Kino qidirish", "📊 Statistika")
        markup.add("✍️ Biz bilan aloqa", "📣 Reklama berish")
        markup.add("👑 Admin Panel")
    else:
        markup.add("🔍 Kino qidirish", "✍️ Biz bilan aloqa")
        markup.add("📣 Reklama berish")
    return markup

# --- KOMANDALARNI QABUL QILISH ---
@bot.message_handler(commands=['start'])
def start(message):
    add_user_to_db(message.from_user.id)
    if check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id, "👋 Xush kelibsiz! Kino kodini yuboring yoki menyudan foydalaning:", reply_markup=get_main_keyboard(message.from_user.id))
    else:
        bot.send_message(message.chat.id, "⚠️ Botdan foydalanish uchun kanallarga a'zo bo'ling:", reply_markup=get_subscription_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "✅ Obuna tasdiqlandi! Kino kodini yuboring yoki menyudan foydalaning:", reply_markup=get_main_keyboard(call.from_user.id))
    else:
        bot.answer_callback_query(call.id, "❌ Kanallarga obuna bo'ling!", show_alert=True)

# --- BAZAGA KINO QO'SHISH FUNKSIYASI (HAR QANDAY USULDA ISHLAYDI) ---
def process_and_save_movie(message, msg_with_file):
    file_id = None
    content_type = None
    caption = msg_with_file.caption if msg_with_file.caption else "Nomsiz kino"

    if msg_with_file.video:
        file_id = msg_with_file.video.file_id
        content_type = 'video'
    elif msg_with_file.document:
        file_id = msg_with_file.document.file_id
        content_type = 'document'
    elif msg_with_file.audio:
        file_id = msg_with_file.audio.file_id
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
            bot.send_message(message.chat.id, f"❌ Bazaga yozishda xato: {e}")
    else:
        bot.send_message(message.chat.id, "❌ Bu xabarda video yoki fayl topilmadi!")

# 1-usul: /add buyrug'i orqali reply qilinganda
@bot.message_handler(commands=['add'])
def add_by_command(message):
    if message.from_user.id != ADMIN_ID: return
    if message.reply_to_message:
        process_and_save_movie(message, message.reply_to_message)
    else:
        bot.send_message(message.chat.id, "❗ Kinoga (video/faylga) REPLY qilib /add deb yozing yoki videoni shunchaki forward qiling!")

# 2-usul: Admin shunchaki video/fayl forward qilsa yoki yuklasa
@bot.message_handler(content_types=['video', 'document', 'audio'])
def add_by_forward(message):
    if message.from_user.id == ADMIN_ID:
        process_and_save_movie(message, message)
    else:
        if not check_subscriptions(message.from_user.id):
            bot.send_message(message.chat.id, "❌ Avval kanallarga obuna bo'ling!", reply_markup=get_subscription_keyboard())

# --- MATNLAR VA TUGMALAR BILAN ISHLASH ---
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    if not check_subscriptions(message.from_user.id): return

    text = message.text

    # 1. Kod bo'yicha qidirish (Faqat raqam bo'lsa)
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
                bot.send_message(message.chat.id, "❌ Fayl o'chib ketgan yoki yuklashda xatolik.")
        else:
            bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi. Qaytadan tekshirib ko'ring.")
        return

    # 2. Tugmalar shartlari
    if text == "🔍 Kino qidirish":
        bot.send_message(message.chat.id, "🔢 Kino kodini yuboring:")

    elif text == "✍️ Biz bilan aloqa":
        msg = bot.send_message(message.chat.id, "✍️ Savol yoki taklifingizni yozib qoldiring. Admin tez orada javob beradi:")
        bot.register_next_step_handler(msg, forward_to_admin)

    elif text == "📣 Reklama berish":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="📈 Arzon Reklama Kanali", url=REKLAMA_KANAL_URL))
        bot.send_message(message.chat.id, "🏷️ Bizning kanallarga reklama berish shartlari va narxlari bilan tanishish uchun quyidagi kanalga o'ting:", reply_markup=markup)

    elif text == "📊 Statistika" and message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, f"📊 BOT STATISTIKASI:\n\n👥 Foydalanuvchilar: {get_users_count()} ta\n🎬 Kinolar: {get_movies_count()} ta")

    elif text == "👑 Admin Panel" and message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📢 Reklama Tarqatish", "🔙 Orqaga")
        bot.send_message(message.chat.id, "👑 Admin Panelga xush kelibsiz:", reply_markup=markup)

    elif text == "📢 Reklama Tarqatish" and message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "📢 Reklama postini (matn, rasm yoki video) yuboring:")
        bot.register_next_step_handler(msg, send_reklama)
        
    elif text == "🔙 Orqaga":
        bot.send_message(message.chat.id, "Bosh menyu:", reply_markup=get_main_keyboard(message.from_user.id))

# --- BIZ BILAN ALOQA FUNKSIYASI ---
def forward_to_admin(message):
    if message.text == "🔙 Orqaga" or message.text in ["🔍 Kino qidirish", "✍️ Biz bilan aloqa", "📣 Reklama berish"]:
        bot.send_message(message.chat.id, "Bekor qilindi.", reply_markup=get_main_keyboard(message.from_user.id))
        return
    try:
        bot.send_message(ADMIN_ID, f"📩 #Xabar\n👤 Kimdan: {message.from_user.first_name} (ID: {message.from_user.id})\n\n✍️ Xabar matni:\n{message.text}")
        bot.send_message(message.chat.id, "✅ Xabaringiz muvaffaqiyatli yetkazildi. Tez orada javob olasiz!", reply_markup=get_main_keyboard(message.from_user.id))
    except:
        bot.send_message(message.chat.id, "❌ Xabarni yetkazishda xatolik yuz berdi.", reply_markup=get_main_keyboard(message.from_user.id))

# --- REKLAMA TARQATISH ---
def send_reklama(message):
    if message.text == "🔙 Orqaga":
        bot.send_message(message.chat.id, "Admin panelga qaytildi.", reply_markup=get_main_keyboard(ADMIN_ID))
        return
    users = get_all_users()
    bot.send_message(message.chat.id, f"🚀 {len(users)} ta foydalanuvchiga reklama yuborish boshlandi...")
    count = 0
    for u_id in users:
        try: 
            bot.copy_message(chat_id=u_id, from_chat_id=message.chat.id, message_id=message.message_id)
            count += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ Reklama tarqatish yakunlandi!\n👥 Yetkazildi: {count} ta foydalanuvchiga.", reply_markup=get_main_keyboard(ADMIN_ID))

if __name__ == "__main__":
    init_db()
    keep_alive()
    bot.infinity_polling()
