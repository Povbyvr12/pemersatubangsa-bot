import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import telegram

BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_ID = -1003034291954  # ID channel utama kamu
CHANNEL_LINK = "https://t.me/pemersatubangsa13868"

CONTENT_FILE_ID = "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA"

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Sudah Join", callback_data="check_join")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup=reply_markup,
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    bot = context.bot

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        status = member.status

        if status in ["member", "administrator", "creator"]:
            await query.message.reply_photo(
                CONTENT_FILE_ID,
                caption="🔥 Terima kasih sudah join! Ini konten spesialnya 💕",
            )
        else:
            await query.message.reply_text(
                "❌ Kamu belum join channel utama! Silakan join dulu ya 👇\n" + CHANNEL_LINK
            )
    except telegram.error.BadRequest:
        await query.message.reply_text(
            "⚠️ Terjadi kesalahan. Pastikan kamu sudah join channel utama kami dulu ya!"
        )


async def on_startup(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook removed, starting polling…")
    except Exception:
        logger.exception("Gagal delete_webhook")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.post_init = on_startup

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
