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
def home(): return "Bot 24/7 Premium rejimda muvaffaqiyatli ishlamoqda!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- SOZLAMALAR ---
# ⚠️ DIQQAT: BotFather bergan yangi xavfsiz tokeningizni kiriting!
TOKEN = "8627886359:AAG4FHpR5tVq3PqL9SnJbJL9fNjaSk78Bcg" 
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 5633684726

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
    current_date = time.strftime("%Y-%m-%d")
    cursor.execute("INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, ?)", (user_id, current_date))
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
    except:
        conn.close()
    return 0

def add_movie_to_db(code, file_id, content_type, caption):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO movies (code, file_id, content_type, caption) VALUES (?, ?, ?, ?)", 
                   (code, file_id, content_type, caption))
    conn.commit()
    conn.close()

def get_movie_from_db(code):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, content_type, caption FROM movies WHERE code=?", (code,))
    result = cursor.fetchone()
    conn.close()
    return result

def search_movies_by_name(query):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT code, caption FROM movies WHERE caption LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()
    conn.close()
    return results

# --- OBUNA TEKSHIRUV ---
def check_subscriptions(user_id):
    if user_id == ADMIN_ID: return True
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def get_subscription_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, ch in enumerate(REQUIRED_CHANNELS, 1):
        markup.add(types.InlineKeyboardButton(text=f"📢 {i}-kanalga obuna bo'lish", url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton(text="📸 Instagram sahifamiz", url=INSTAGRAM_URL))
    markup.add(types.InlineKeyboardButton(text="✅ Obunani tasdiqlash", callback_data="check_subs"))
    return markup

# --- DINAMIK MENYU (ADMIN VA FOYDALANUVCHI AJRATILDI) ---
def get_main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if user_id == ADMIN_ID:
        # Admin uchun xavfsiz va to'liq maxfiy menyu (Statistika faqat shu yerda)
        markup.add("🔍 Kino qidirish", "📊 Statistika")
        markup.add("✍️ Biz bilan aloqa (Xabarlar)")
        markup.add("👑 Admin Panel")
    else:
        # Oddiy foydalanuvchilar menyusi (Statistika umuman ko'rinmaydi)
        markup.add("🔍 Kino qidirish")
        markup.add("✍️ Biz bilan aloqa")
    return markup

# --- KOMANDALAR ---
@bot.message_handler(commands=['start'])
def start(message):
    add_user_to_db(message.from_user.id)
    
    if check_subscriptions(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"👋 Assalomu alaykum, {message.from_user.first_name}!\n\n🎬 Kino kodini yuboring yoki quyidagi menyudan foydalaning:",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    else:
        bot.send_message(
            message.chat.id,
            "⚠️ Botdan to'liq foydalanish uchun hamkor kanallarimizga obuna bo'lishingiz shart:",
            reply_markup=get_subscription_keyboard()
        )

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check(call):
    if check_subscriptions(call.from_user.id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(
            call.message.chat.id, 
            "✅ Obuna tasdiqlandi! Xush kelibsiz. Kino kodini yuboring yoki menyudan foydalaning:", 
            reply_markup=get_main_keyboard(call.from_user.id)
        )
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)

# --- MATNLAR BILAN ISHLASH VA MENYU NAZORATI ---
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    if not check_subscriptions(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Avval kanallarga obuna bo'ling!", reply_markup=get_subscription_keyboard())
        return

    text = message.text

    # 1. Kino kodini avtomatik tekshirish
    if text.isdigit():
        movie_data = get_movie_from_db(text)
        if movie_data:
            file_id, c_type, caption = movie_data
            try:
                caption_text = f"🎬 Kod: {text}\n\n🎥 Nomi: {caption if caption else 'Nomsiz kino'}"
                if c_type == 'video':
                    bot.send_video(message.chat.id, file_id, caption=caption_text)
                elif c_type == 'document':
                    bot.send_document(message.chat.id, file_id, caption=caption_text)
                elif c_type == 'audio':
                    bot.send_audio(message.chat.id, file_id, caption=caption_text)
            except:
                bot.send_message(message.chat.id, "❌ Xato: Fayl o'chirib yuborilgan yoki yuborishda muammo bor.")
        else:
            bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi. Qaytadan tekshirib ko'ring.")
        return

    # 2. Umumiy menyu amallari
    if text == "🔍 Kino qidirish":
        msg = bot.send_message(message.chat.id, "✍️ Qidirayotgan kinongiz nomini yoki kalit so'zni yuboring:")
        bot.register_next_step_handler(msg, process_search)
    
    elif text == "✍️ Biz bilan aloqa":
        msg = bot.send_message(message.chat.id, "✍️ Adminga yubormoqchi bo'lgan xabaringiz yoki taklifingizni yozing:")
        bot.register_next_step_handler(msg, process_feedback)

    # 🔒 FAOL XAVFSIZLIK: STATISTIKA FAQAT ADMIN UCHUN ISHLAYDI
    elif text == "📊 Statistika":
        if message.from_user.id == ADMIN_ID:
            u_count = get_users_count()
            m_count = get_movies_count()
            bot.send_message(
                message.chat.id, 
                f"📊 *MUKAMMAL BOT STATISTIKASI:*\n\n"
                f"👥 Jami foydalanuvchilar: `{u_count}` ta\n"
                f"🎬 Saqlangan kinolar soni: `{m_count}` ta\n"
                f"⏱️ Tizim serveri holati: `Onlayn (24/7 Ultra)`",
                parse_mode="Markdown"
            )
        else:
            # Oddiy foydalanuvchi qandaydir yo'l bilan buni yozsa ham baza berkitiladi
            bot.send_message(message.chat.id, "⚠️ Kechirasiz, ushbu sahifa faqat bot asoschisi uchun xizmat qiladi!")

    # 👑 ADMIN PANEL VA FUNKSIYALARI
    elif message.from_user.id == ADMIN_ID:
        if text == "👑 Admin Panel":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            markup.add("📢 Reklama Tarqatish", "🔙 Asosiy Menyuga Qaytish")
            bot.send_message(message.chat.id, "👑 Admin boshqaruv paneli:", reply_markup=markup)
            
        elif text == "📢 Reklama Tarqatish":
            msg = bot.send_message(message.chat.id, "📢 Reklama xabarini (matn, rasm, video yoki tayyor forward) yuboring:")
            bot.register_next_step_handler(msg, send_reklama_to_all)
            
        elif text == "✍️ Biz bilan aloqa (Xabarlar)":
            bot.send_message(message.chat.id, "ℹ️ Bu bo'lim orqali foydalanuvchilar sizga yuborgan takliflarni shaxsiy profilingizda qabul qilasiz.")
            
        elif text == "🔙 Asosiy Menyuga Qaytish":
            bot.send_message(message.chat.id, "🔙 Asosiy menyuga qaytdingiz.", reply_markup=get_main_keyboard(message.from_user.id))

# --- KINO QIDIRISH ALGORITMI ---
def process_search(message):
    query = message.text
    if len(query) < 3:
        bot.send_message(message.chat.id, "⚠️ Qidiruv so'zi kamida 3 ta harfdan iborat bo'lishi kerak!")
        return
    
    results = search_movies_by_name(query)
    if results:
        text = f"🔍 *'{query}' bo'yicha topilgan kinolar ro'yxati:*\n\n"
        for code, caption in results:
            short_caption = caption[:35] + "..." if len(caption) > 35 else caption
            text += f"🔢 Kod: `{code}` — {short_caption}\n"
        text += "\n🍿 Kinoni tomosha qilish uchun uning kodini botga raqam shaklida yuboring."
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"🤷‍♂️ Afsuski, bazamizdan '{query}' bo'yicha hech qanday kino topilmadi.")

# --- FOYDALANUVCHIDAN ADMINGA ALOQA TIZIMI ---
def process_feedback(message):
    user_text = message.text
    if user_text:
        try:
            bot.send_message(
                ADMIN_ID, 
                f"📩 *YANGI MUROJAAT #Aloqa*\n\n"
                f"👤 *Kimdan:* {message.from_user.first_name}\n"
                f"🆔 *User ID:* `{message.from_user.id}`\n"
                f"💬 *Xabar matni:* {user_text}",
                parse_mode="Markdown"
            )
            bot.send_message(message.chat.id, "✅ Murojaatingiz adminga muvaffaqiyatli yetkazildi. Tez orada javob olasiz!")
        except:
            bot.send_message(message.chat.id, "❌ Xabarni yetkazishda xatolik yuz berdi. Keyinroq qayta urinib ko'ring.")

# --- MULTIMEDIA BILAN ISHLASH (/add komandasi uchun) ---
@bot.message_handler(commands=['add'])
def add_movie(message):
    if message.from_user.id != ADMIN_ID: return
    if not message.reply_to_message:
        bot.send_message(message.chat.id, "❗ Kinoga (video/fayl) reply qilib /add yozing")
        return

    msg = message.reply_to_message
    file_id = None
    content_type = None
    caption = msg.caption if msg.caption else "Nomsiz kino"

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
            add_movie_to_db(new_code, file_id, content_type, caption)
            bot.send_message(message.chat.id, f"✅ Baza muvaffaqiyatli saqlandi!\n🎬 Kino kodi: `{new_code}`\n🎥 Nomi: {caption}", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(message.chat.id, f"Xato: {e}")
    else:
        bot.send_message(message.chat.id, "❗ Faqat video, audio yoki fayl turidagi xabarlarni saqlash mumkin.")

# --- INTELLEKTUAL REKLAMA TARQATISH PANELI ---
def send_reklama_to_all(message):
    users = get_all_users()
    success = 0
    failed = 0
    
    status_msg = bot.send_message(message.chat.id, f"⏳ Reklama tarqatilmoqda (Jami: {len(users)} ta faol manzil)...")
    
    for u_id in users:
        try:
            bot.copy_message(chat_id=u_id, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
            time.sleep(0.05) 
        except:
            failed += 1
            
    bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        text=f"📢 *REKLAMA TARQATISH YAKUNLANDI:*\n\n✅ Muvaffaqiyatli yetkazildi: `{success}` ta foydalanuvchiga\n❌ Bloklaganlar/O'chib ketganlar: `{failed}` ta",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(ADMIN_ID)
    )

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    init_db()
    print("🤖 Premium Super-Bot 100% quvvat bilan ishga tushdi...")
    keep_alive()
    bot.infinity_polling()
