import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.error import TelegramError

# Bot token
BOT_TOKEN = "7081602239:AAFw4NEloriZ2c5MDH6LfS9HBJ5AiWCje9w"

# Admin ID
ADMIN_ID = 5978600106

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ma'lumotlar bazasi funksiyalari
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS movies
                 (id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, description TEXT, file_id TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins
                 (id INTEGER PRIMARY KEY, user_id INTEGER UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS channels
                 (id INTEGER PRIMARY KEY, channel_id TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS statistics
                 (id INTEGER PRIMARY KEY, command TEXT, usage_count INTEGER)''')
    conn.commit()
    conn.close()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def add_movie(name: str, code: str, description: str, file_id: str) -> bool:
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO movies (name, code, description, file_id) VALUES (?, ?, ?, ?)",
                  (name, code, description, file_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_movie(code: str):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM movies WHERE code = ?", (code,))
    movie = c.fetchone()
    conn.close()
    if movie:
        return {"id": movie[0], "name": movie[1], "code": movie[2], "description": movie[3], "file_id": movie[4]}
    return None

def get_statistics():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute("SELECT command, usage_count FROM statistics")
    stats = c.fetchall()
    conn.close()
    return stats

def update_statistics(command: str):
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute("SELECT usage_count FROM statistics WHERE command = ?", (command,))
    record = c.fetchone()
    if record:
        new_count = record[0] + 1
        c.execute("UPDATE statistics SET usage_count = ? WHERE command = ?", (new_count, command))
    else:
        c.execute("INSERT INTO statistics (command, usage_count) VALUES (?, ?)", (command, 1))
    conn.commit()
    conn.close()

# Admin paneli
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat adminlar uchun.")
        return
    
    keyboard = [
        [KeyboardButton("📊 Statistika"), KeyboardButton("🎬 Kino qo'shish")],
        [KeyboardButton("📝 Kino tahrirlash"), KeyboardButton("📢 Reklama yuborish")],
        [KeyboardButton("🔗 Kanalni qo'shish yoki o'chirish")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Admin paneliga xush kelibsiz. Quyidagi tugmalardan foydalaning:", reply_markup=reply_markup)

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat adminlar uchun.")
        return
    
    stats = get_statistics()
    statistics_text = "Statistika:\n\n"
    for stat in stats:
        statistics_text += f"{stat[0]}: {stat[1]} marta ishlatilgan\n"
    
    await update.message.reply_text(statistics_text)

async def add_movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat adminlar uchun.")
        return ConversationHandler.END
    
    await update.message.reply_text("Kino nomini kiriting:")
    return MOVIE_NAME

async def movie_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['movie_name'] = update.message.text
    await update.message.reply_text("Kino uchun unikal kod kiriting:")
    return MOVIE_CODE

async def movie_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['movie_code'] = update.message.text
    await update.message.reply_text("Kino haqida qisqacha ma'lumot kiriting:")
    return MOVIE_DESCRIPTION

async def movie_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['movie_description'] = update.message.text
    await update.message.reply_text("Kino faylini yuboring:")
    return MOVIE_FILE

async def movie_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    file = update.message.document or update.message.video
    if file:
        file_id = file.file_id
        if add_movie(context.user_data['movie_name'], context.user_data['movie_code'], 
                     context.user_data['movie_description'], file_id):
            await update.message.reply_text("Kino muvaffaqiyatli qo'shildi.")
        else:
            await update.message.reply_text("Xatolik yuz berdi. Kod takrorlanishi mumkin.")
    else:
        await update.message.reply_text("Fayl yuborilmadi. Jarayon bekor qilindi.")
    
    return ConversationHandler.END

async def advertisement_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Reklama matnini yuborish
    advertisement = update.message.text
    # Reklama yuborish logikasini qo'shing
    await update.message.reply_text(f"Reklama matni yuborildi:\n\n{advertisement}")
    return ConversationHandler.END

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Bu buyruq faqat adminlar uchun.")
        return
    
    # Kanalni qo'shish yoki o'chirish
    await update.message.reply_text("Kanal linkini kiriting (misol: @example_channel):")
    context.user_data['channel_action'] = "add"
    return CHANNEL_LINK

async def handle_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    channel_link = update.message.text
    # Kanal qo'shish yoki o'chirish logikasini qo'shing
    await update.message.reply_text(f"Kanal qo'shildi yoki o'chirildi: {channel_link}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Jarayon bekor qilindi.")
    return ConversationHandler.END

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Botga xush kelibsiz! Foydalanuvchilar uchun filmlar va boshqa xizmatlar bilan tanishish mumkin.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🎬 Filmlar"), KeyboardButton("📊 Statistika")]], resize_keyboard=True
        )
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Yordam kerak bo'lsa, bu yerda yordam olish mumkin.\n\n"
        "Buyruqlar:\n"
        "/start - Botni ishga tushirish\n"
        "/admin_panel - Admin paneliga kirish"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Foydalanuvchi yuborgan xabarni qayta ishlash
    text = update.message.text
    await update.message.reply_text(f"Siz yozgan xabar: {text}")

# Conversation states
MOVIE_NAME, MOVIE_CODE, MOVIE_DESCRIPTION, MOVIE_FILE, ADVERTISEMENT_TEXT, CHANNEL_LINK = range(6)

# Asosiy funksiya
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    
    init_db()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("admin_panel", admin_panel)],
        states={
            MOVIE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, movie_name)],
            MOVIE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, movie_code)],
            MOVIE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, movie_description)],
            MOVIE_FILE: [MessageHandler(filters.ATTACHMENT, movie_file)],
            ADVERTISEMENT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, advertisement_text)],
            CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_link)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
