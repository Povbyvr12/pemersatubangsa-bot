import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# KONFIG
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_ID = -1003034291954
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

# Konten yang dikirim setelah join
FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join Channel", url=CHANNEL_JOIN_URL)],
        [InlineKeyboardButton("✅ Sudah Join", callback_data="joined")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup=kb()
    )


async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Silakan join channel dulu ya 👇", reply_markup=kb())


async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception:
        pass

    joined = False
    last_err = None
    for _ in range(3):
        try:
            member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
            if member.status in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
                ChatMemberStatus.RESTRICTED,
            ):
                joined = True
                break
        except Exception as e:
            last_err = e
        await asyncio.sleep(2)

    await update.callback_query.answer()

    if not joined:
        if last_err:
            logger.warning(f"Join check error: {last_err}")
        await update.callback_query.message.reply_text(
            "❌ Kamu belum join channel utama! Silakan join dulu ya 👇",
            reply_markup=kb()
        )
        return

    try:
        for fid in FILE_IDS:
            await context.bot.send_photo(chat_id=chat_id, photo=fid)
        await update.callback_query.message.reply_text(
            "🔥 Terima kasih sudah join! Ini konten spesialnya 💕"
        )
    except Exception as e:
        logger.exception(f"Gagal kirim konten: {e}")
        await update.callback_query.message.reply_text(
            "⚠️ Ada kendala saat kirim konten. Coba /start lalu tekan 'Sudah Join' lagi ya."
        )


async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    if msg.photo:
        fid = msg.photo[-1].file_id
        kind = "📸 Photo"
    elif msg.video:
        fid = msg.video.file_id
        kind = "🎬 Video"
    elif msg.document:
        fid = msg.document.file_id
        kind = "📄 Document"
    else:
        return

    await msg.reply_text(f"{kind} file_id:\n<code>{fid}</code>", parse_mode="HTML")


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
    app.add_handler(CallbackQueryHandler(handle_joined, pattern=r"^joined$"))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.Document.ALL,
        handle_media
    ))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
