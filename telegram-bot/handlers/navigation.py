"""Navigation handlers for Telegram bot"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.formatter import format_book_message
from state import StateManager


async def handle_navigation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handle navigation button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    state_manager = StateManager()
    
    if not state_manager.has_state(user_id):
        await query.edit_message_text(
            "❌ Сессия истекла. Пожалуйста, начните новый поиск."
        )
        return
    
    user_state = state_manager.get_state(user_id)
    callback_data = query.data
    
    if callback_data == "prev_book":
        if user_state.can_go_prev():
            user_state.go_prev()
            await update_book_message(query, user_state)
        else:
            await query.answer("Это первая книга", show_alert=False)
    
    elif callback_data == "next_book":
        if user_state.can_go_next():
            user_state.go_next()
            await update_book_message(query, user_state)
        else:
            await query.answer("Это последняя книга", show_alert=False)
    
    elif callback_data == "new_search":
        state_manager.clear_state(user_id)
        await query.edit_message_text(
            "🔄 Начните новый поиск, отправив мне ваш запрос!"
        )


async def update_book_message(query, user_state):
    """Update book message with new book and navigation buttons"""
    current_book = user_state.get_current_book()
    if not current_book:
        await query.edit_message_text("Книга не найдена.")
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
            InlineKeyboardButton("← Назад", callback_data="prev_book")
        )
    
    # Next button
    if user_state.can_go_next():
        buttons_row.append(
            InlineKeyboardButton("Далее →", callback_data="next_book")
        )
    else:
        # Last book - show "New Search" button
        buttons_row.append(
            InlineKeyboardButton("🔄 Новый поиск", callback_data="new_search")
        )
    
    if buttons_row:
        keyboard.append(buttons_row)
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    # Update message
    await query.edit_message_text(
        message_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

