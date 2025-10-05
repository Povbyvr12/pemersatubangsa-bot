import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ============== KONFIG ==============
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"

# Pakai USERNAME channel (paling stabil)
CHANNEL_USERNAME = "@pemersatubangsa13868"
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

# Daftar konten yang dikirim SETELAH join
FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]
# ====================================

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

async def _has_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> tuple[bool, str|None]:
    """
    Cek status member di channel berbasis USERNAME.
    Return (joined, err_text)
    """
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        status = member.status
        if status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.RESTRICTED,
        ):
            return True, None
        # status LEFT / KICKED dll -> belum join
        return False, None
    except Exception as e:
        # Simpan error singkat buat debug
        return False, f"{type(e).__name__}: {e}"

async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception:
        pass

    # Retry lebih panjang biar stabil (mis. user baru join 1-2 detik lalu)
    last_err = None
    joined = False
    for _ in range(6):  # 6x
        joined, err_txt = await _has_joined(context, user.id)
        if joined:
            break
        last_err = err_txt
        await asyncio.sleep(2)

    # tutup loading tombol
    await cq.answer()

    if not joined:
        # Kalau errornya jelas bukan "belum join", tampilkan short debug
        extra = f"\n\n(Info teknis: {last_err})" if last_err else ""
        await cq.message.reply_text(
            "❌ Kamu belum join channel utama! Silakan join dulu ya 👇" + extra,
            reply_markup=kb(),
        )
        return

    # Sudah join -> kirim konten
    try:
        for fid in FILE_IDS:
            await context.bot.send_photo(chat_id=chat_id, photo=fid)
        await cq.message.reply_text("🔥 Terima kasih sudah join! Ini konten spesialnya 💕")
    except Exception as e:
        logger.exception("Gagal kirim konten")
        await cq.message.reply_text(
            "⚠️ Ada kendala saat kirim konten. Coba /start lalu tekan 'Sudah Join' lagi ya."
        )

# Kirim file_id saat owner mengirim media ke bot (buat nyatet FILE_IDS baru)
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

# Opsional: /debug_join buat cek statusmu sekarang
async def debug_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ok, err = await _has_joined(context, update.effective_user.id)
    txt = "JOINED ✅" if ok else "NOT JOINED ❌"
    if err:
        txt += f"\n(Info teknis: {err})"
    await update.message.reply_text(txt)

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
    app.add_handler(CommandHandler("debug_join", debug_join))  # opsional
    app.add_handler(CallbackQueryHandler(handle_joined, pattern=r"^joined$"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
