import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_ID = "-100248813868"
CHANNEL_LINK = "https://t.me/+FBO14eOGdi45OTRl"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup={
            "inline_keyboard": [
                [{"text": "🔥 Join Channel", "url": CHANNEL_LINK}],
                [{"text": "✅ Sudah Join", "callback_data": "check_join"}],
            ]
        }
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Klik link ini untuk join channel resmi kami 👇\n\n🔥 {CHANNEL_LINK}")

async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return
    file_id = update.message.photo[-1].file_id
    await update.message.reply_text(f"📸 file_id:\n`{file_id}`", parse_mode="Markdown")

async def on_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.video:
        return
    file_id = update.message.video.file_id
    await update.message.reply_text(f"🎬 file_id:\n`{file_id}`", parse_mode="Markdown")

async def on_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.document:
        return
    file_id = update.message.document.file_id
    await update.message.reply_text(f"📄 file_id:\n`{file_id}`", parse_mode="Markdown")

async def on_startup(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook removed, starting polling…")
    except Exception:
        logger.exception("Gagal delete_webhook")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.VIDEO, on_video))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
