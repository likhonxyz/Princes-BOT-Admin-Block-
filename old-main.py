from keep_alive import keep_alive
keep_alive()
import re
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

# Token সরাসরি এখানে বসানো হয়েছে
TOKEN = "7945756761:AAH9rgtEx3eOfZWGto-JD1A5DjM1MHOlflA"

# Logging সেটআপ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# No-exempt list per group
group_no_exempt_admin_ids = {}

# Link detection regex
link_pattern = re.compile(r"(http[s]?://|t\.me/)", re.IGNORECASE)

async def delete_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    chat_administrators = await update.effective_chat.get_administrators()
    admin_ids = [admin.user.id for admin in chat_administrators]

    no_exempt_list = group_no_exempt_admin_ids.get(chat_id, [])

    # Admin ra link dite parbe normally, anonymous admin ra parbe na
    # Anonymous admin detection: user.is_anonymous (True hole anonymous admin)
    if user.id in admin_ids and user.id not in no_exempt_list and not user.is_anonymous:
        return

    if update.message and link_pattern.search(update.message.text or ""):
        try:
            await update.message.delete()
            await update.message.reply_text("❌ Links are not allowed!")
        except Exception as e:
            logger.warning(f"Error deleting message: {e}")

async def add_no_exempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /addnoexempt <group_id> <user_id>")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])

        if chat_id not in group_no_exempt_admin_ids:
            group_no_exempt_admin_ids[chat_id] = []

        if user_id not in group_no_exempt_admin_ids[chat_id]:
            group_no_exempt_admin_ids[chat_id].append(user_id)
            await update.message.reply_text(f"✅ User ID {user_id} added to no-exempt list for group {chat_id}.")
        else:
            await update.message.reply_text(f"ℹ️ User ID {user_id} already in no-exempt list for group {chat_id}.")
    except ValueError:
        await update.message.reply_text("❌ Invalid IDs.")

async def remove_no_exempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /removenoexempt <group_id> <user_id>")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])

        if chat_id in group_no_exempt_admin_ids and user_id in group_no_exempt_admin_ids[chat_id]:
            group_no_exempt_admin_ids[chat_id].remove(user_id)
            await update.message.reply_text(f"✅ User ID {user_id} removed from no-exempt list for group {chat_id}.")
        else:
            await update.message.reply_text(f"ℹ️ User ID {user_id} not found in no-exempt list for group {chat_id}.")
    except ValueError:
        await update.message.reply_text("❌ Invalid IDs.")

async def list_no_exempt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage: /listnoexempt <group_id>")
        return
    try:
        chat_id = int(context.args[0])
        if chat_id not in group_no_exempt_admin_ids or not group_no_exempt_admin_ids[chat_id]:
            await update.message.reply_text(f"ℹ️ No user IDs in no-exempt list for group {chat_id}.")
        else:
            ids_text = "\n".join(str(uid) for uid in group_no_exempt_admin_ids[chat_id])
            await update.message.reply_text(f"📝 No-exempt list for group {chat_id}:\n{ids_text}")
    except ValueError:
        await update.message.reply_text("❌ Invalid group ID.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running and ready!\nYou can control me via private chat using group IDs.")

app = ApplicationBuilder().token(TOKEN).build()

# Command handlers
app.add_handler(CommandHandler("addnoexempt", add_no_exempt))
app.add_handler(CommandHandler("removenoexempt", remove_no_exempt))
app.add_handler(CommandHandler("listnoexempt", list_no_exempt))
app.add_handler(CommandHandler("start", start))

# Message handler for links
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), delete_links))

logger.info("✅ Bot is running...")
app.run_polling()
