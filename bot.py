import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_LINK = "https://t.me/+FBO14eOGdi45OTRl"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- command /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi PEMERSATU BANGSA 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇\n\n"
        f"{CHANNEL_LINK}"
    )

# --- command /join ---
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Klik link ini untuk join channel resmi kami 👇\n\n🔥 {CHANNEL_LINK}"
    )

# --- ambil file_id (foto, video, dokumen) ---
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        kind = "📸 Foto"
    elif update.message.video:
        file_id = update.message.video.file_id
        kind = "🎬 Video"
    elif update.message.document:
        file_id = update.message.document.file_id
        kind = "📄 Dokumen"
    else:
        return

    await update.message.reply_text(
        f"{kind} file_id kamu adalah:\n<code>{file_id}</code>",
        parse_mode="HTML"
    )

# --- saat bot mulai ---
async def on_startup(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook removed, starting polling…")
    except Exception:
        logger.exception("Gagal delete_webhook")

# --- main program ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join))

    # Media handler (buat ambil file_id)
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media))

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
