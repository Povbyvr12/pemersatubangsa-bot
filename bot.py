import logging
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ================== KONFIG ==================
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_USERNAME = "@pemersatubangsa13868"
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

# 2 konten awal (sekali saat lolos join)
FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]

# 2 konten harian (bergantian tiap kirim)
DAILY_CONTENTS = [
    {
        "file_id": "AgACAgUAAxkBAAOnaOJci2VklCBxzhLAp3Ma9EH6hg4AAkoLaxuuWhlXtK03QigD7wgBAAMCAAN4AAM2BA",
        "caption": "💥 BONUS BESAR TANPA SYARAT! 💥\nDeposit 100K → Bonus 20K langsung masuk! ⚡\n💰 Total saldo main 120K, profit bisa WD hari ini juga!\n👉 dapatkan sebelum promo berakhir!\n\nLINK LOGIN PROFIT 🔗 https://heylink.me/kedai168login/"
    },
    {
        "file_id": "AgACAgUAAxkBAAOpaOJclgqPDDZgzqQFTwsE37XOeXkAAksLaxuuWhlX-mB7ruEuyWoBAAMCAAN4AAM2BA",
        "caption": "🚨 BONUS 100 + 20 CUMA HARI INI! 🚨\nDeposit 100K → saldo langsung jadi 120K 🤑\n⚡ Langsung auto masuk!\n🎰 Main sekarang, profit bisa cair cepat hari ini juga!\n\nLINK LOGIN PROFIT 🔗 https://heylink.me/kedai168login/"
    },
]

SEND_HOURS = [11, 13, 15, 17, 19, 21]  # WIB
WIB = ZoneInfo("Asia/Jakarta")

USERS_FILE = Path("joined_users.txt")
INIT_SENT_FILE = Path("init_sent.txt")
# ===========================================

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join Channel", url=CHANNEL_JOIN_URL)],
        [InlineKeyboardButton("✅ Sudah Join", callback_data="joined")],
    ])


def _read_ids(path: Path):
    if not path.exists():
        return set()
    return {int(x) for x in path.read_text().splitlines() if x.strip().isdigit()}


def _append_id(path: Path, uid: int):
    ids = _read_ids(path)
    if uid not in ids:
        with path.open("a") as f:
            f.write(f"{uid}\n")


async def _has_joined(context, user_id: int):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        status = getattr(member, "status", "")
        return status in ("member", "administrator", "creator", "owner", "restricted")
    except Exception as e:
        logger.warning(f"get_chat_member error: {e}")
        return False


# ==== Commands ====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup=kb()
    )


async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    user = update.effective_user
    chat_id = user.id

    await cq.answer()
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # cek join (maks 3x)
    ok = False
    for _ in range(3):
        if await _has_joined(context, user.id):
            ok = True
            break
        await asyncio.sleep(1.5)

    if not ok:
        await cq.message.reply_text("❌ Kamu belum join channel utama! Silakan join dulu ya 👇", reply_markup=kb())
        return

    _append_id(USERS_FILE, user.id)

    sent_init = _read_ids(INIT_SENT_FILE)
    if user.id not in sent_init:
        for fid in FILE_IDS:
            try:
                await context.bot.send_photo(chat_id=chat_id, photo=fid)
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning(f"Gagal kirim konten awal ke {chat_id}: {e}")
        _append_id(INIT_SENT_FILE, user.id)

    await cq.message.reply_text("🔥 Terima kasih sudah join! langsung klik kontennya dan nikmati servicenya bersama kami 💕")


# ==== Auto reply saat user kirim chat random ====
async def fallback_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo kak 👋\n"
        "Ada yang bisa dibantu?\n\n"
        "Kalau mau langsung login bisa lewat link ini ya:\n"
        "👉 https://heylink.me/kedai168login/\n\n"
        "Kalau sudah, kabari di sini untuk konfirmasi ya kak 😊"
    )


# ==== Broadcast Loop (WIB) ====
async def broadcast_loop(app):
    await asyncio.sleep(5)
    last_hour = None
    while True:
        now = datetime.now(WIB)
        hour = now.hour

        if hour in SEND_HOURS and hour != last_hour:
            users = list(_read_ids(USERS_FILE))
            if users:
                content = DAILY_CONTENTS[(hour // 2) % len(DAILY_CONTENTS)]
                fid = content["file_id"]
                caption = content.get("caption")

                logger.info(f"[{now.strftime('%H:%M')}] Kirim ke {len(users)} user...")
                for uid in users:
                    try:
                        await app.bot.send_photo(chat_id=uid, photo=fid, caption=caption)
                        await asyncio.sleep(0.4)
                    except Exception as e:
                        logger.warning(f"Gagal kirim ke {uid}: {e}")

                last_hour = hour
        await asyncio.sleep(30)


async def on_startup(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    asyncio.create_task(broadcast_loop(app))


# ==== Main ====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_joined, pattern=r"^joined$"))

    # tambahkan auto-reply
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & ~filters.COMMAND,
            fallback_reply
        )
    )

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
