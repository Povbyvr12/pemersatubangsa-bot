from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# === ISI TOKEN & CHANNEL DI SINI ===
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_ID = "pemersatubangsa13868"  # tanpa @

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Untuk lihat file & konten terbaru, pastikan sudah join channel resmi kami dulu ya 💕"
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Klik link ini untuk join channel resmi kami 👇\n\n🔥 https://t.me/{CHANNEL_ID}"
    )

# Hapus webhook dulu supaya polling tidak konflik (409)
async def on_startup(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("join", join))

# Pastikan webhook dibersihkan saat inisialisasi
app.post_init = on_startup

if __name__ == "__main__":
    app.run_polling(allowed_updates=Update.ALL_TYPES)
