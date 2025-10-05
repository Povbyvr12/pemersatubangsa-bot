import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_LINK = "https://t.me/+FBO14eOGdi45OTRl"
CHANNEL_ID = -1001234567890
TEST_FILE_ID = "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

def join_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔥 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Sudah Join", callback_data="check_join")]
        ]
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup=join_keyboard()
    )

async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Klik link ini untuk join channel resmi kami 👇\n\n🔥 {CHANNEL_LINK}",
        reply_markup=join_keyboard()
    )

async def on_check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        status = member.status
    except Exception as e:
        logger.exception("Gagal cek keanggotaan: %s", e)
        status = "unknown"

    if status in ("member", "administrator", "creator"):
        if TEST_FILE_ID:
            await query.message.reply_photo(TEST_FILE_ID, caption="Makasih sudah join! 🎉")
        else:
            await query.message.reply_text("Makasih sudah join! 🎉")
    else:
        await query.message.reply_text(
            "Kamu belum terdeteksi join channel.\nSilakan join dulu ya 👇",
            reply_markup=join_keyboard()
        )

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg.photo:
        file_id = msg.photo[-1].file_id
        kind = "📸 Photo"
    elif msg.video:
        file_id = msg.video.file_id
        kind = "🎬 Video"
    elif msg.document:
        file_id = msg.document.file_id
        kind = "📄 Document"
    else:
        return
    await msg.reply_text(f"{kind} file_id:\n`{file_id}`", parse_mode="Markdown")

async def on_startup(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook removed, starting polling…")
    except Exception:
        logger.exception("Gagal delete_webhook")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CallbackQueryHandler(on_check_join, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
