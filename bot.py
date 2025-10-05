import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# === GANTI SESUAI PUNYA KAMU ===
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_LINK = "https://t.me/+FBO14eOGdi45OTRl"  # link join channel kamu

# Setup logging (buat monitoring error di Railway)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Sudah Join", callback_data="verify")]
    ])
    await update.message.reply_text(text, reply_markup=keyboard)

# Command /join
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join Channel", url=CHANNEL_LINK)]
    ])
    await update.message.reply_text("Klik tombol di bawah untuk join 👇", reply_markup=keyboard)

# Callback kalau user klik “Sudah Join”
async def on_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Terima kasih! Kalau sudah join, kamu bisa kirim /start lagi ya 😉")

# Saat bot mulai jalan
async def on_startup(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook removed, starting polling…")
    except Exception:
        logger.exception("Gagal delete_webhook")

# Fungsi utama
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CallbackQueryHandler(on_verify, pattern="^verify$"))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
