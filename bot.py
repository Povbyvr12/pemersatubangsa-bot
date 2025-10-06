import logging, asyncio
from datetime import time as dtime
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = "8093048850:AAHFyMUXZKlawgJzoTJg89g06uUuUpLBn78"
CHANNEL_USERNAME = "@pemersatubangsa13868"
CHANNEL_JOIN_URL = "https://t.me/pemersatubangsa13868"

FILE_IDS = [
    "AgACAgUAAxkBAAN3aOIv1uuLkn96kWkJ6tF0Qcst7kcAAlAMaxuuWhFXY5A63iHcezABAAMCAAN4AAM2BA",
    "AgACAgUAAxkBAAOBaOJFbIZvqFO5hzpXEmoayF4zeK0AAh8LaxuuWhlXxyDFA-MZjn8BAAMCAAN4AAM2BA",
]

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

async def _has_joined(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.RESTRICTED,
        )
    except Exception:
        return False

async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    except Exception:
        pass

    joined = False
    for _ in range(6):
        if await _has_joined(context, user.id):
            joined = True
            break
        await asyncio.sleep(2)
    await cq.answer()

    if not joined:
        await cq.message.reply_text("❌ Kamu belum join channel utama! Silakan join dulu ya 👇", reply_markup=kb())
        return

    with open("joined_users.txt", "a", encoding="utf-8") as f:
        f.write(str(chat_id) + "\n")

    for fid in FILE_IDS:
        await context.bot.send_photo(chat_id=chat_id, photo=fid)
    await cq.message.reply_text("🔥 Terima kasih sudah join! Konten baru akan dikirim otomatis setiap 2 jam 💕")

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

async def broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    idx = context.job.data.get("slot_index", 0)
    try:
        with open("joined_users.txt", "r", encoding="utf-8") as f:
            users = [int(u.strip()) for u in f if u.strip()]
    except FileNotFoundError:
        users = []
    if not users:
        return
    content = INIT_CONTENTS[idx % len(INIT_CONTENTS)]
    for uid in users:
        try:
            await context.bot.send_photo(chat_id=uid, photo=content["file_id"], caption=content["caption"])
            await asyncio.sleep(0.4)
        except Exception:
            continue
    logger.info(f"Broadcast {idx} selesai ke {len(users)} user.")

async def on_startup(app):
    await app.bot.delete_webhook(drop_pending_updates=True)
    tz = ZoneInfo("Asia/Jakarta")
    jam_kirim = [11, 13, 15, 17, 19, 21]
    for i, jam in enumerate(jam_kirim):
        app.job_queue.run_daily(
            broadcast_job,
            time=dtime(hour=jam, minute=0, tzinfo=tz),
            data={"slot_index": i},
            name=f"broadcast-{jam}"
        )
    logger.info("Bot aktif & jadwal broadcast sudah diset.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_joined, pattern=r"^joined$"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, handle_media))
    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
