"""Command handlers for Telegram bot"""
from telegram import Update
from telegram.ext import ContextTypes
from state import StateManager


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = (
        "👋 Привет! Я бот для поиска книг.\n\n"
        "Просто напишите мне, что вы хотите почитать, и я найду для вас подходящие книги!\n\n"
        "Например:\n"
        "• \"книги про роботов\"\n"
        "• \"научная фантастика\"\n"
        "• \"детективы\"\n\n"
        "Используйте /help для получения справки."
    )
    
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📚 <b>Справка по использованию бота</b>\n\n"
        "🔍 <b>Поиск книг:</b>\n"
        "Просто напишите ваш запрос, и я найду подходящие книги.\n\n"
        "📖 <b>Навигация:</b>\n"
        "После получения результатов используйте кнопки для просмотра книг:\n"
        "• <b>Далее →</b> - следующая книга\n"
        "• <b>← Назад</b> - предыдущая книга\n"
        "• <b>Новый поиск</b> - начать новый поиск\n\n"
        "🧹 <b>Команды:</b>\n"
        "/start - начать работу\n"
        "/help - показать эту справку\n"
        "/clear - очистить текущий поиск"
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command"""
    state_manager = StateManager()
    user_id = update.effective_user.id
    
    if state_manager.has_state(user_id):
        state_manager.clear_state(user_id)
        await update.message.reply_text(
            "✅ Текущий поиск очищен. Можете начать новый поиск!"
        )
    else:
        await update.message.reply_text(
            "ℹ️ У вас нет активного поиска для очистки."
        )

