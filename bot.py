import logging
import asyncio
import datetime
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================== KONFIG ==================
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_USERNAME = "@pemersatubangsa13868"
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

# Konten awal (dikirim SEKALI saat user pertama kali lolos join)
FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]

# Konten harian (bergantian tiap kirim) + caption
INIT_CONTENTS = [
    {
        "file_id": "AgACAgUAAxkBAAOnaOJci2VklCBxzhLAp3Ma9EH6hg4AAkoLaxuuWhlXtK03QigD7wgBAAMCAAN4AAM2BA",
        "caption": "💥 BONUS BESAR TANPA SYARAT! 💥\nDeposit 100K → Bonus 20K langsung masuk! ⚡\n💰 Total saldo main 120K, profit bisa WD hari ini juga!\n👉 dapatkan sebelum promo berakhir!"
    },
    {
        "file_id": "AgACAgUAAxkBAAOpaOJclgqPDDZgzqQFTwsE37XOeXkAAksLaxuuWhlX-mB7ruEuyWoBAAMCAAN4AAM2BA",
        "caption": "🚨 BONUS 100 + 20 CUMA HARI INI! 🚨\nDeposit 100K → saldo langsung jadi 120K 🤑\n⚡ Gak perlu nunggu event, langsung auto masuk!\n🎰 Main sekarang, profit bisa cair cepat hari ini juga!"
    },
]

SEND_HOURS = [11, 13, 15, 17, 19, 21]  # jam kirim otomatis
USERS_FILE = Path("joined_users.txt")
INIT_SENT_FILE = Path("init_sent.txt")
# ===========================================

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


def _read_id_set(path: Path) -> set[int]:
    if not path.exists():
        return set()
    return {int(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip().isdigit()}


def _append_id(path: Path, user_id: int):
    ids = _read_id_set(path)
    if user_id not in ids:
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{user_id}\n")


async def _has_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        m = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        # bandingkan string status, biar aman lintas versi PTB
        return str(getattr(m, "status", "")) in {"member", "administrator", "creator", "owner", "restricted"}
    except Exception as e:
        logger.warning(f"get_chat_member error for {user_id}: {e}")
        return False


# ===== Commands & Callbacks =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup=kb()
    )


async def joined_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id

    await cq.answer()
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception:
        pass

    # retry kecil untuk delay Telegram
    ok = False
    for _ in range(4):
        if await _has_joined(context, user.id):
            ok = True
            break
        await asyncio.sleep(1.5)

    if not ok:
        await cq.message.reply_text("❌ Kamu belum join channel utama! Silakan join dulu ya 👇", reply_markup=kb())
        return

    # simpan user
    _append_id(USERS_FILE, user.id)

    # kirim KONTEN AWAL (FILE_IDS) sekali per user
    sent_init_users = _read_id_set(INIT_SENT_FILE)
    if user.id not in sent_init_users:
        for fid in FILE_IDS:
            try:
                await context.bot.send_photo(chat_id=chat_id, photo=fid)
                await asyncio.sleep(0.4)
            except Exception as e:
                logger.warning(f"Gagal kirim konten awal ke {user.id}: {e}")
        _append_id(INIT_SENT_FILE, user.id)

    await cq.message.reply_text("🔥 Terima kasih sudah join! Konten baru akan dikirim otomatis setiap 2 jam 💕")


# ===== Auto broadcast 6× sehari =====
async def broadcast_loop(app):
    await asyncio.sleep(10)
    last_sent_hour = None
    while True:
        now = datetime.datetime.now()
        hour = now.hour

        if hour in SEND_HOURS and hour != last_sent_hour:
            users = list(_read_id_set(USERS_FILE))
            if users:
                content = INIT_CONTENTS[(hour // 2) % len(INIT_CONTENTS)]
                file_id = content["file_id"]
                caption = content.get("caption") or None

                sent = 0
                for uid in users:
                    try:
                        await app.bot.send_photo(chat_id=uid, photo=file_id, caption=caption)
                        sent += 1
                        await asyncio.sleep(0.4)
                    except Exception as e:
                        logger.warning(f"Gagal kirim ke {uid}: {e}")

                logger.info(f"[{hour:02d}:00] Broadcast terkirim ke {sent} user.")
            else:
                logger.info(f"[{hour:02d}:00] Belum ada user yang join.")

            last_sent_hour = hour

        await asyncio.sleep(30)


async def on_startup(app):
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    asyncio.create_task(broadcast_loop(app))


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(joined_pressed, pattern=r"^joined$"))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
