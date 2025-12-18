import re
import logging
import sqlite3
import os
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)
from telegram import Update

# ================= CONFIG =================
TOKEN = "7945756761:AAH9rgtEx3eOfZWGto-JD1A5DjM1MHOlflA"

# Zeabur volume mount path (FINAL)
DATA_DIR = "/app/data"
DB_NAME = f"{DATA_DIR}/no_exempt.db"

# ================= ENSURE DATA DIR =================
os.makedirs(DATA_DIR, exist_ok=True)

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= DATABASE =================
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS no_exempt (
    group_id INTEGER,
    user_id INTEGER,
    PRIMARY KEY (group_id, user_id)
)
""")
conn.commit()

def add_no_exempt_db(group_id, user_id):
    cursor.execute(
        "INSERT OR IGNORE INTO no_exempt (group_id, user_id) VALUES (?, ?)",
        (group_id, user_id),
    )
    conn.commit()

def remove_no_exempt_db(group_id, user_id):
    cursor.execute(
        "DELETE FROM no_exempt WHERE group_id=? AND user_id=?",
        (group_id, user_id),
    )
    conn.commit()

def get_no_exempt_list(group_id):
    cursor.execute(
        "SELECT user_id FROM no_exempt WHERE group_id=?",
        (group_id,),
    )
    return [row[0] for row in cursor.fetchall()]

# ================= LINK FILTER =================
link_pattern = re.compile(r"(http[s]?://|t\.me/)", re.IGNORECASE)

async def delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    message = update.message
    if not message or not message.text:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user

    admins = await update.effective_chat.get_administrators()
    admin_ids = [a.user.id for a in admins]

    no_exempt_list = get_no_exempt_list(chat_id)

    is_anonymous_admin = (
        message.from_user is None and message.sender_chat is not None
    )

    if (
        user
        and user.id in admin_ids
        and user.id not in no_exempt_list
        and not is_anonymous_admin
    ):
        return

    if link_pattern.search(message.text):
        try:
            await message.delete()
            await message.reply_text("❌ Links are not allowed!")
        except Exception as e:
            logger.warning(e)

# ================= COMMANDS (PRIVATE ONLY) =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    await update.message.reply_text(
        "𝙾𝙽𝙻𝚈 ⏤͟͟͞͞𓆩̥•🇧𝙴𝚁𝙻𝙸𝙽⟁⃤ 😈 𝙲𝙰𝙽 𝙲𝙾𝙽𝚃𝚁𝙾𝙻 𝚃𝙷𝙸𝚂 𝙱𝙾𝚃"
    )

async def add_no_exempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addnoexempt <group_id> <user_id>")
        return

    try:
        add_no_exempt_db(int(context.args[0]), int(context.args[1]))
        await update.message.reply_text("✅ Added.")
    except ValueError:
        await update.message.reply_text("❌ Invalid ID.")

async def remove_no_exempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /removenoexempt <group_id> <user_id>")
        return

    try:
        remove_no_exempt_db(int(context.args[0]), int(context.args[1]))
        await update.message.reply_text("✅ Removed.")
    except ValueError:
        await update.message.reply_text("❌ Invalid ID.")

async def list_no_exempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /list <group_id>")
        return

    try:
        group_id = int(context.args[0])
        user_ids = get_no_exempt_list(group_id)

        if not user_ids:
            await update.message.reply_text("ℹ️ Empty list.")
            return

        text = "📝 <b>No-Exempt Admin List</b>\n\n"
        for i, uid in enumerate(user_ids, start=1):
            try:
                member = await context.bot.get_chat_member(group_id, uid)
                name = member.user.full_name
                text += f"{i:02d}- <a href='tg://user?id={uid}'>{name}</a> [{uid}]\n"
            except Exception:
                text += f"{i:02d}- Unknown User [{uid}]\n"

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except ValueError:
        await update.message.reply_text("❌ Invalid group ID.")

# ================= APP =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addnoexempt", add_no_exempt))
app.add_handler(CommandHandler("removenoexempt", remove_no_exempt))
app.add_handler(CommandHandler("list", list_no_exempt))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, delete_links))

logger.info("Bot started successfully (Zeabur Volume FIXED)")
app.run_polling()
