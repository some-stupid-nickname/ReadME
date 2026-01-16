"""Search handler for Telegram bot"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.api_client import APIClient
from utils.parser import parse_llm_response
from utils.formatter import format_intro_message, format_book_message
from state import StateManager


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search query from user"""
    user_id = update.effective_user.id
    query = update.message.text.strip()
    
    if not query:
        await update.message.reply_text(
            "Please enter a search query."
        )
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    try:
        # Call API
        api_client = APIClient()
        search_response = await api_client.search_books(query)
        
        # Parse LLM response
        parsed = parse_llm_response(
            search_response.response,
            len(search_response.books)
        )
        
        # Save state
        state_manager = StateManager()
        user_state = state_manager.get_state(user_id)
        user_state.intro_message = parsed['intro']
        user_state.books = search_response.books
        user_state.recommendations = parsed['recommendations']
        user_state.current_book_index = 0
        user_state.search_query = query
        
        # Send intro message
        intro_text = format_intro_message(user_state.intro_message)
        await update.message.reply_text(intro_text)
        
        # Send first book with navigation buttons
        await send_book_message(update, context, user_state)
        
    except Exception as e:
        error_message = (
            "❌ An error occurred while searching for books.\n\n"
            "Please try again later or modify your query."
        )
        await update.message.reply_text(error_message)
        # Log error in production
        print(f"Search error for user {user_id}: {str(e)}")


async def send_book_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_state
):
    """Send book message with navigation buttons"""
    current_book = user_state.get_current_book()
    if not current_book:
        await update.message.reply_text("Book not found.")
        return
    
    # Format book message
    recommendation = user_state.get_current_recommendation()
    current = user_state.current_book_index + 1
    total = len(user_state.books)
    
    message_text = format_book_message(
        current_book,
        recommendation,
        current,
        total
    )
    
    # Create navigation buttons
    keyboard = []
    buttons_row = []
    
    # Previous button
    if user_state.can_go_prev():
        buttons_row.append(
            InlineKeyboardButton("← Back", callback_data="prev_book")
        )
    
    # Next button
    if user_state.can_go_next():
        buttons_row.append(
            InlineKeyboardButton("Next →", callback_data="next_book")
        )
    else:
        # Last book - show "New Search" button
        buttons_row.append(
            InlineKeyboardButton("🔄 New Search", callback_data="new_search")
        )
    
    if buttons_row:
        keyboard.append(buttons_row)
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    # Send message
    await update.message.reply_text(
        message_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )
