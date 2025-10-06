import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from zoneinfo import ZoneInfo

# === KONFIGURASI ===
BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_USERNAME = "@pemersatubangsa13868"
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

# Konten awal (dikirim setelah join)
FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]

# Konten otomatis (setiap 2 jam)
INIT_CONTENTS = [
    {
        "file_id": "AgACAgUAAxkBAAOnaOJci2VklCBxzhLAp3Ma9EH6hg4AAkoLaxuuWhlXtK03QigD7wgBAAMCAAN4AAM2BA",
        "caption": "💥 BONUS BESAR TANPA SYARAT! 💥\nDeposit 100K → Bonus 20K langsung masuk! ⚡\n💰 Total saldo main 120K, profit bisa WD hari ini juga!\n👉 Dapatkan sebelum promo berakhir!"
    },
    {
        "file_id": "AgACAgUAAxkBAAOpaOJclgqPDDZgzqQFTwsE37XOeXkAAksLaxuuWhlX-mB7ruEuyWoBAAMCAAN4AAM2BA",
        "caption": "🚨 BONUS 100 + 20 CUMA HARI INI! 🚨\nDeposit 100K → saldo langsung jadi 120K 🤑\n⚡ Langsung auto masuk!\n🎰 Main sekarang, profit bisa cair cepat hari ini juga!"
    },
]

# Timezone
WIB = ZoneInfo("Asia/Jakarta")

# Logging setup
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Keyboard
def kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Join Channel", url=CHANNEL_JOIN_URL)],
        [InlineKeyboardButton("✅ Sudah Join", callback_data="joined")],
    ])

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! 🔥 Selamat datang di bot resmi pemersatubangsa168138 💕\n\n"
        "Untuk lihat file & konten terbaru, pastikan kamu sudah join channel resmi kami dulu ya 👇",
        reply_markup=kb()
    )

# /join command
async def join_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Silakan join channel dulu ya 👇", reply_markup=kb())

# Cek apakah user sudah join
async def has_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
            ChatMemberStatus.RESTRICTED,
        ]
    except Exception as e:
        logger.warning(f"Join check error: {e}")
        return False

# Ketika user klik “Sudah Join”
async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id
    await query.answer()

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    joined = await has_joined(context, user.id)

    if not joined:
        await query.message.reply_text(
            "❌ Kamu belum join channel utama! Silakan join dulu ya 👇",
            reply_markup=kb()
        )
        return

    # Kirim dua konten awal
    for fid in FILE_IDS:
        await context.bot.send_photo(chat_id=chat_id, photo=fid)

    await query.message.reply_text("🔥 Terima kasih sudah join! Konten baru akan dikirim otomatis setiap 2 jam 💕")

    # Simpan user ID untuk broadcast
    if "joined_users" not in context.bot_data:
        context.bot_data["joined_users"] = set()
    context.bot_data["joined_users"].add(chat_id)

# Fungsi kirim broadcast otomatis
async def send_auto_content(context: ContextTypes.DEFAULT_TYPE):
    users = context.bot_data.get("joined_users", set())
    if not users:
        return

    now = datetime.now(WIB)
    idx = now.hour // 2 % len(INIT_CONTENTS)
    content = INIT_CONTENTS[idx]

    for uid in users:
        try:
            await context.bot.send_photo(
                chat_id=uid,
                photo=content["file_id"],
                caption=content["caption"]
            )
        except Exception as e:
            logger.warning(f"Gagal kirim ke {uid}: {e}")

# Ambil file_id
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
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

# Jalankan bot
async def on_startup(app):
    scheduler = AsyncIOScheduler(timezone=WIB)

    # Jadwal otomatis (11, 13, 15, 17, 19, 21 WIB)
    for hour in [11, 13, 15, 17, 19, 21]:
        scheduler.add_job(send_auto_content, "cron", hour=hour, minute=0, args=[app])

    scheduler.start()
    logger.info("Scheduler dimulai.")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join_cmd))
    app.add_handler(CallbackQueryHandler(handle_joined, pattern="^joined$"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
