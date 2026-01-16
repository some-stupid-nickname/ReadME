"""Command handlers for Telegram bot"""
from telegram import Update
from telegram.ext import ContextTypes
from state import StateManager


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_text = (
        "👋 Hi! I'm a book search bot.\n\n"
        "Just tell me what you'd like to read, and I'll find suitable books for you!\n\n"
        "For example:\n"
        "• \"books about robots\"\n"
        "• \"science fiction\"\n"
        "• \"mystery novels\"\n\n"
        "Use /help for more information."
    )
    
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "📚 <b>Bot User Guide</b>\n\n"
        "🔍 <b>Book Search:</b>\n"
        "Just type your query, and I'll find suitable books.\n\n"
        "📖 <b>Navigation:</b>\n"
        "After receiving results, use buttons to browse books:\n"
        "• <b>Next →</b> - next book\n"
        "• <b>← Back</b> - previous book\n"
        "• <b>New Search</b> - start a new search\n\n"
        "🧹 <b>Commands:</b>\n"
        "/start - start the bot\n"
        "/help - show this help\n"
        "/clear - clear current search"
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command"""
    state_manager = StateManager()
    user_id = update.effective_user.id
    
    if state_manager.has_state(user_id):
        state_manager.clear_state(user_id)
        await update.message.reply_text(
            "✅ Current search cleared. You can start a new search!"
        )
    else:
        await update.message.reply_text(
            "ℹ️ You don't have an active search to clear."
        )
