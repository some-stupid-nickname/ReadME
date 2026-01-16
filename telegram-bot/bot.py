"""Main Telegram bot file"""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from config import TELEGRAM_BOT_TOKEN
from handlers import commands, search, navigation

import re

class TokenSafeFormatter(logging.Formatter):
    """Formatter that hides bot tokens in log messages"""
    def format(self, record):
        # Get the formatted message
        message = super().format(record)
        # Replace bot token pattern in the message
        message = re.sub(
            r'/bot[\d]+:[A-Za-z0-9_-]+',
            '/bot***TOKEN***',
            message
        )
        return message

# Configure logging with token-safe formatter
handler = logging.StreamHandler()
handler.setFormatter(TokenSafeFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)
logger = logging.getLogger(__name__)

# Also apply filter to httpx logger for extra safety
httpx_logger = logging.getLogger("httpx")

class TokenFilter(logging.Filter):
    """Filter to hide bot tokens in logs"""
    def filter(self, record):
        import re
        # Replace bot token in message
        if hasattr(record, 'msg') and record.msg:
            record.msg = re.sub(
                r'/bot[\d]+:[A-Za-z0-9_-]+',
                '/bot***TOKEN***',
                str(record.msg)
            )
        # Replace in args if present
        if hasattr(record, 'args') and record.args:
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    new_args.append(re.sub(
                        r'/bot[\d]+:[A-Za-z0-9_-]+',
                        '/bot***TOKEN***',
                        arg
                    ))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        return True

httpx_logger.addFilter(TokenFilter())


def main():
    """Initialize and run the bot"""
    # Validate token before creating application
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_BOT_TOKEN.strip():
        logger.error("TELEGRAM_BOT_TOKEN is not set or empty!")
        raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env file")
    
    logger.info(f"Initializing bot with token: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    # Create application with increased timeouts
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )
    
    # Register command handlers
    application.add_handler(CommandHandler("start", commands.start_command))
    application.add_handler(CommandHandler("help", commands.help_command))
    application.add_handler(CommandHandler("clear", commands.clear_command))
    
    # Register callback query handler (for navigation buttons)
    application.add_handler(
        CallbackQueryHandler(navigation.handle_navigation_callback)
    )
    
    # Register message handler (for search queries)
    # Handle all text messages that are not commands
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            search.handle_search
        )
    )
    
    # Error handler
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later."
                )
            except Exception:
                pass
    
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting bot...")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise


if __name__ == "__main__":
    main()

