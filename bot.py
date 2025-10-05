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

# ================== KONFIG ==================
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"

# Pakai USERNAME channel (lebih stabil), harus diawali '@'
CHANNEL_USERNAME = "@pemersatubangsa13868"
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

# Konten yang dikirim setelah terdeteksi join
FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]
# ============================================

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("gatebot")

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

async def _is_joined(bot, user_id: int) -> bool:
    """Cek keanggotaan user di channel username; retry singkat agar responsif."""
    for _ in range(2):  # cepat & cukup
        m = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if m.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.RESTRICTED,
        ):
            return True
        await asyncio.sleep(0.8)
    return False

async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id

    # animasi “typing” biar nggak terlihat freeze
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception:
        pass

    try:
        joined = await _is_joined(context.bot, user.id)
    except Exception as e:
        # Kalau gagal akses (mis. bot bukan admin/terblokir), kasih pesan jelas
        await q.answer()
        log.warning(f"get_chat_member error: {type(e).__name__}: {e}")
        await q.message.reply_text(
            "⚠️ Bot gagal baca status kamu. Pastikan bot **admin** di channel. "
            "Coba /start lagi setelah 10 detik.",
            reply_markup=kb()
        )
        return

    await q.answer()

    if not joined:
        await q.message.reply_text(
            "❌ Kamu belum join channel utama! Silakan join dulu ya 👇",
            reply_markup=kb()
        )
        return

    # Kirim konten
    try:
        for fid in FILE_IDS:
            await context.bot.send_photo(chat_id=chat_id, photo=fid)
        await q.message.reply_text("🔥 Terima kasih sudah join! Ini konten spesialnya 💕")
    except Exception as e:
        log.exception(f"Gagal kirim konten: {e}")
        await q.message.reply_text(
            "⚠️ Ada kendala saat kirim konten. Coba /start lalu tekan 'Sudah Join' lagi ya."
        )

# Util: balikin file_id saat kamu push media ke bot (biar gampang nambah konten)
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return
    if msg.photo:
        fid, kind = msg.photo[-1].file_id, "📸 Photo"
    elif msg.video:
        fid, kind = msg.video.file_id, "🎬 Video"
    elif msg.document:
        fid, kind = msg.document.file_id, "📄 Document"
    else:
        return
    await msg.reply_text(f"{kind} file_id:\n<code>{fid}</code>", parse_mode="HTML")

# Debug cepat: /check -> lihat status yang dibaca bot
async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        m = await context.bot.get_chat_member(CHANNEL_USERNAME, update.effective_user.id)
        await update.message.reply_text(f"Status kamu di {CHANNEL_USERNAME}: {m.status}")
    except Exception as e:
        await update.message.reply_text(f"Check gagal: {type(e).__name__}")

async def on_startup(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    log.info("Bot ready.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CommandHandler("check", check_cmd))  # opsional, buat diagnosa
    app.add_handler(CallbackQueryHandler(handle_joined, pattern=r"^joined$"))
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media
    ))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
