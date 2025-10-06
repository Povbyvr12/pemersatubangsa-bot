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

CHANNEL_USERNAME = "@pemersatubangsa13868"
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

# Kirim SETELAH join (2 konten awal)
FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]

# Kirim otomatis (bergantian) 6x/hari
AUTO_CONTENTS = [
    {
        "file_id": "AgACAgUAAxkBAAOnaOJci2VklCBxzhLAp3Ma9EH6hg4AAkoLaxuuWhlXtK03QigD7wgBAAMCAAN4AAM2BA",
        "caption": "💥 BONUS BESAR TANPA SYARAT! 💥\nDeposit 100K → Bonus 20K langsung masuk! ⚡\n💰 Total saldo main 120K, profit bisa WD hari ini juga!\n👉 Dapatkan sebelum promo berakhir!"
    },
    {
        "file_id": "AgACAgUAAxkBAAOpaOJclgqPDDZgzqQFTwsE37XOeXkAAksLaxuuWhlX-mB7ruEuyWoBAAMCAAN4AAM2BA",
        "caption": "🚨 BONUS 100 + 20 CUMA HARI INI! 🚨\nDeposit 100K → saldo langsung jadi 120K 🤑\n⚡ Langsung auto masuk!\n🎰 Main sekarang, profit bisa cair cepat hari ini juga!"
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup=kb()
    )


async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Silakan join channel dulu ya 👇", reply_markup=kb())


async def _has_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        m = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return m.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,         # (OWNER = pemilik)
            ChatMemberStatus.RESTRICTED,
        )
    except Exception as e:
        logger.warning(f"get_chat_member error: {e}")
        return False


async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id

    await cq.answer()
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception:
        pass

    # retry beberapa kali agar stabil
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

    # kirim 2 konten awal
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


async def send_auto_content(context: ContextTypes.DEFAULT_TYPE):
    users = context.bot_data.get("joined_users", set())
    if not users:
        return

    # pilih konten bergantian berdasarkan jam
    now_hour = int(asyncio.get_event_loop().time())  # dummy seed
    content = AUTO_CONTENTS[now_hour % len(AUTO_CONTENTS)]

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
    # jadwalkan 6x per hari (WIB) pakai JobQueue bawaan PTB
    for h in SEND_HOURS:
        app.job_queue.run_daily(
            send_auto_content,
            time=dtime(hour=h, minute=0, tzinfo=WIB),
            name=f"auto_{h}"
        )
    logger.info("JobQueue terpasang untuk 11,13,15,17,19,21 WIB.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CallbackQueryHandler(handle_joined, pattern=r"^joined$"))

    # optional: bantu ambil file_id kalau kirim media ke bot
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, lambda u, c: u.message.reply_text(
        f"{'📸' if u.message.photo else '🎬' if u.message.video else '📄'} file_id:\n<code>"
        f"{(u.message.photo[-1].file_id if u.message.photo else u.message.video.file_id if u.message.video else u.message.document.file_id)}</code>",
        parse_mode="HTML"
    )))

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
