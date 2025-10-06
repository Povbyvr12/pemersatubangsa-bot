import logging
import asyncio
from datetime import time as dtime
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ===== KONFIG =====
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"

# Pakai USERNAME channel (stabil)
CHANNEL_USERNAME = "@pemersatubangsa13868"
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

# 2 konten awal (dikirim setelah user terverifikasi join)
FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]

# Konten otomatis 2 jam sekali (bergantian)
AUTO_CONTENTS = [
    {
        "file_id": "AgACAgUAAxkBAAOnaOJci2VklCBxzhLAp3Ma9EH6hg4AAkoLaxuuWhlXtK03QigD7wgBAAMCAAN4AAM2BA",
        "caption": "💥 BONUS BESAR TANPA SYARAT! 💥\nDeposit 100K → Bonus 20K ⚡\n💰 Saldo 120K, profit bisa WD hari ini juga!\n👉 Dapatkan sebelum promo berakhir!"
    },
    {
        "file_id": "AgACAgUAAxkBAAOpaOJclgqPDDZgzqQFTwsE37XOeXkAAksLaxuuWhlX-mB7ruEuyWoBAAMCAAN4AAM2BA",
        "caption": "🚨 BONUS 100 + 20 CUMA HARI INI! 🚨\nDeposit 100K → saldo jadi 120K 🤑\n⚡ Langsung auto masuk!\n🎰 Main sekarang, profit cair cepat!"
    },
]

WIB = ZoneInfo("Asia/Jakarta")
SEND_HOURS = [11, 13, 15, 17, 19, 21]
# ==================

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


# ========== Commands ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup=kb()
    )

async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Silakan join channel dulu ya 👇", reply_markup=kb())


# ========== Helpers ==========
async def _has_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Cek status member via username channel (PTB 21.x)."""
    try:
        m = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,      # PTB 21.x pakai OWNER, bukan CREATOR
            ChatMemberStatus.RESTRICTED,
        )
    except Exception as e:
        logger.warning(f"get_chat_member error: {e}")
        return False


# ========== Callback tombol "Sudah Join" ==========
async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id

    await cq.answer()

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception:
        pass

    # retry sampai 6x (supaya tidak false-negative kalau user baru join)
    joined = False
    for _ in range(6):
        if await _has_joined(context, user.id):
            joined = True
            break
        await asyncio.sleep(2)

    if not joined:
        await cq.message.reply_text(
            "❌ Kamu belum join channel utama! Silakan join dulu ya 👇",
            reply_markup=kb()
        )
        return

    # Kirim 2 konten awal
    for fid in FILE_IDS:
        try:
            await context.bot.send_photo(chat_id=chat_id, photo=fid)
        except Exception as e:
            logger.warning(f"Gagal kirim welcome ke {chat_id}: {e}")

    await cq.message.reply_text(
        "🔥 Terima kasih sudah join! Konten baru akan dikirim otomatis setiap 2 jam 💕"
    )

    # simpan user untuk broadcast
    context.bot_data.setdefault("joined_users", set()).add(chat_id)


# ========== JobQueue (auto kirim 2 jam sekali di jam fix) ==========
async def send_auto_content(context: ContextTypes.DEFAULT_TYPE):
    users = context.bot_data.get("joined_users", set())
    if not users:
        return

    # pilih konten bergiliran
    # gunakan jam sekarang agar berpindah tiap run
    idx = (asyncio.get_running_loop().time() // 1) % len(AUTO_CONTENTS)
    content = AUTO_CONTENTS[int(idx)]

    for uid in list(users):
        try:
            await context.bot.send_photo(
                chat_id=uid,
                photo=content["file_id"],
                caption=content["caption"]
            )
        except Exception as e:
            logger.warning(f"Kirim auto ke {uid} gagal: {e}")


async def on_startup(app):
    # Jadwalkan 6x per hari (WIB) pakai JobQueue bawaan PTB
    for h in SEND_HOURS:
        app.job_queue.run_daily(
            send_auto_content,
            time=dtime(hour=h, minute=0, tzinfo=WIB),
            name=f"auto_{h}"
        )
    logger.info("JobQueue terpasang (11,13,15,17,19,21 WIB).")


# ========== Optional: handler untuk ambil file_id ==========
async def media_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# ========== Bootstrap ==========
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CallbackQueryHandler(handle_joined, pattern=r"^joined$"))

    # helper ambil file_id (opsional)
    app.add_handler(MessageHandler(
        filters.PHOTO | filters.VIDEO | filters.Document.ALL, media_file_id
    ))

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
