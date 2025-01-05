from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import sqlite3
import logging

# Bot token
BOT_TOKEN = "7081602239:AAFw4NEloriZ2c5MDH6LfS9HBJ5AiWCje9w"
ADMIN_ID = 5978600106

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Suhbat holatlari
MOVIE_NAME, MOVIE_CODE, MOVIE_DESCRIPTION, MOVIE_FILE = range(4)

# Database functions
def get_user_count() -> int:
    """Get the count of all users in the database."""
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_movie_count() -> int:
    """Get the count of all movies in the database."""
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM movies")
    count = c.fetchone()[0]
    conn.close()
    return count

def add_channel(channel_id: str) -> bool:
    """Add a channel to the database."""
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO channels (channel_id) VALUES (?)", (channel_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def remove_channel(channel_id: str) -> bool:
    """Remove a channel from the database."""
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
    return True

def get_channels() -> list:
    """Get a list of all channels."""
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT channel_id FROM channels")
    channels = [row[0] for row in c.fetchall()]
    conn.close()
    return channels

# Admin panel
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the admin panel."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bu buyruq faqat adminlar uchun.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("🎥 Kino joylash/taxrirlash", callback_data="manage_movies")],
        [InlineKeyboardButton("📢 Reklama yuborish", callback_data="send_advertisement")],
        [InlineKeyboardButton("📢 Kanal qo'shish/o'chirish", callback_data="manage_channels")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Admin paneliga xush kelibsiz! Quyidagi tugmalardan birini tanlang:", reply_markup=reply_markup)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin panel callback queries."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "stats":
        user_count = get_user_count()
        movie_count = get_movie_count()
        await query.edit_message_text(f"📊 Statistika:\n\n👤 Foydalanuvchilar soni: {user_count}\n🎥 Kinolar soni: {movie_count}")
    elif query.data == "manage_movies":
        await query.edit_message_text("🎥 Kino boshqarish funksiyasi hozircha rivojlanmoqda.")
    elif query.data == "send_advertisement":
        await query.edit_message_text("📢 Reklama yuborish funksiyasi hozircha rivojlanmoqda.")
    elif query.data == "manage_channels":
        channels = get_channels()
        if not channels:
            await query.edit_message_text("📢 Hozircha hech qanday kanal qo'shilmagan.")
        else:
            channels_text = "\n".join([f"📌 {channel}" for channel in channels])
            await query.edit_message_text(f"📢 Qo'shilgan kanallar:\n\n{channels_text}")

# Main function
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(handle_admin_callback))
    
    application.run_polling()

if __name__ == '__main__':
    main()
