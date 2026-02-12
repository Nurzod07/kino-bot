import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 🔑 Bu yerga o'z tokeningni yoz
TOKEN = "7750050629:AAH_-gwPFiMu6lg8Ny6xvBXA6JNHf02uSy4"

# 📢 Majburiy obuna kanallari
CHANNELS = [
    "@telefon_reklama_xizmati",
    "@bekhruz_pubgm",
    "@inglizchaonlayntestlar"
]

# 🎬 Maxfiy kino kanali
PRIVATE_CHANNEL = "@timj7J_IKGpiMzZi"

# 📊 Statistikani saqlash
STARTED_USERS = set()       # /start bosganlar
CODE_COUNTERS = {}          # har kod nechta odam ishlatgan

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    STARTED_USERS.add(user.id)
    # Majburiy kanallarga obuna tekshirish
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user.id)
            if member.status not in ["member", "administrator", "creator"]:
                await update.message.reply_text(f"Iltimos {channel} kanaliga obuna bo‘ling.")
                return
        except:
            await update.message.reply_text(f"{channel} kanalini tekshirib bo‘lmadi.")
            return
    await update.message.reply_text("Salom! Kino kodi yuboring 🎬")

# /statistika komandasi
async def statistik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"Botni {len(STARTED_USERS)} ta foydalanuvchi ishlatgan ✅\n\n"
    if CODE_COUNTERS:
        for code, count in CODE_COUNTERS.items():
            text += f"Kod {code}: {count} ta foydalanuvchi\n"
    else:
        text += "Hali hech kim kod ishlatmagan."
    await update.message.reply_text(text)

# Kino kodini tekshirish va private kanaldan forward qilish
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    # Kod uchun statistika
    if code in CODE_COUNTERS:
        CODE_COUNTERS[code] += 1
    else:
        CODE_COUNTERS[code] = 1
    # Private kanaldan postni topib forward qilish
    try:
        async for msg in context.bot.get_chat(PRIVATE_CHANNEL).iter_history(limit=50):
            if f"Kod: {code}" in (msg.text or ""):
                await msg.forward(chat_id=update.effective_chat.id)
                return
        await update.message.reply_text("Noto‘g‘ri kod ❌")
    except Exception as e:
        await update.message.reply_text("Xatolik yuz berdi yoki bot kanalni ko‘rolmayapti.")

# 🔧 Bot ishga tushirish
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("statistika", statistik))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_code))

print("Bot ishga tushdi ✅")
app.run_polling()
