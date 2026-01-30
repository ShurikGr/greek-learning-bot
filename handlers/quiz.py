"""
Quiz command handlers.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from services.quiz_service import quiz_service
from services.stats_service import stats_service
from database.db import db

logger = logging.getLogger(__name__)


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quiz command - send single quiz question."""
    user = update.effective_user

    # Generate quiz
    quiz_data = quiz_service.generate_quiz(user.id)

    if not quiz_data:
        await update.message.reply_text(
            "❌ Недостаточно слов в базе для создания квиза.\n"
            "Попросите админа добавить больше слов."
        )
        return

    # Store quiz data in context for answer checking
    context.user_data['current_quiz'] = quiz_data

    # Create inline keyboard with answer options
    keyboard = []
    for i, answer in enumerate(quiz_data['answers']):
        keyboard.append([InlineKeyboardButton(answer, callback_data=f"answer_{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send quiz question
    direction_emoji = "🇬🇷→🇷🇺" if quiz_data['direction'] == 'GR→RU' else "🇷🇺→🇬🇷"
    await update.message.reply_text(
        f"{direction_emoji} {quiz_data['direction']}\n\n"
        f"❓ {quiz_data['question']}\n\n"
        f"Выберите правильный ответ:",
        reply_markup=reply_markup
    )

    logger.info(f"User {user.id} started quiz for word_id {quiz_data['word_id']}")


async def quiz_session_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quiz_session - start continuous quiz session."""
    user = update.effective_user

    # Check if user already has active session
    query = "SELECT quiz_session_active FROM users WHERE user_id = ?"
    results = db.execute_query(query, (user.id,))

    if results and results[0]['quiz_session_active']:
        await update.message.reply_text(
            "⚠️ У вас уже активна сессия квиза.\n"
            "Используйте /stop для остановки."
        )
        return

    # Mark session as active
    db.execute_update(
        "INSERT OR REPLACE INTO users (user_id, username, first_name, quiz_session_active) VALUES (?, ?, ?, 1)",
        (user.id, user.username, user.first_name)
    )

    await update.message.reply_text(
        "🎯 Сессия квиза начата!\n\n"
        "Отвечайте на вопросы один за другим.\n"
        "Используйте /stop для остановки.\n\n"
        "Приготовьтесь..."
    )

    # Send first question
    await quiz_command(update, context)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop - stop quiz session."""
    user = update.effective_user

    # Mark session as inactive
    db.execute_update(
        "UPDATE users SET quiz_session_active = 0 WHERE user_id = ?",
        (user.id,)
    )

    # Get final stats
    stats = stats_service.get_user_stats(user.id)

    await update.message.reply_text(
        f"🛑 Сессия квиза остановлена.\n\n"
        f"📊 Финальная статистика:\n"
        f"Правильных ответов: {stats['total_correct']}/{stats['total_questions']} "
        f"({stats['success_rate']}%)\n\n"
        f"Отличная работа! 💪"
    )

    logger.info(f"User {user.id} stopped quiz session")


async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle answer button callback."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Get stored quiz data
    quiz_data = context.user_data.get('current_quiz')
    if not quiz_data:
        await query.edit_message_text("❌ Ошибка: данные квиза не найдены. Попробуйте /quiz снова.")
        return

    # Parse answer index from callback data
    answer_index = int(query.data.split('_')[1])

    # Check if answer is correct
    is_correct = quiz_service.check_answer(quiz_data, answer_index)

    # Record answer in statistics
    stats_service.record_answer(user.id, quiz_data['word_id'], is_correct)

    # Prepare response
    if is_correct:
        response = f"✅ Правильно!\n\n"
    else:
        correct_answer = quiz_data['answers'][quiz_data['correct_index']]
        response = f"❌ Неправильно.\n\nПравильный ответ: {correct_answer}\n\n"

    # Add stats
    stats = stats_service.get_user_stats(user.id)
    response += (
        f"📊 Ваша статистика:\n"
        f"Правильных ответов: {stats['total_correct']}/{stats['total_questions']} "
        f"({stats['success_rate']}%)\n\n"
        f"Используйте /quiz для следующего вопроса"
    )

    await query.edit_message_text(response)

    # Clear quiz data
    context.user_data['current_quiz'] = None

    # Check if user has active session
    query_check = "SELECT quiz_session_active FROM users WHERE user_id = ?"
    results = db.execute_query(query_check, (user.id,))

    if results and results[0]['quiz_session_active']:
        # Send next question automatically
        import asyncio
        await asyncio.sleep(1)  # Small delay

        # Generate and send next quiz
        quiz_data = quiz_service.generate_quiz(user.id)
        if quiz_data:
            context.user_data['current_quiz'] = quiz_data

            keyboard = []
            for i, answer in enumerate(quiz_data['answers']):
                keyboard.append([InlineKeyboardButton(answer, callback_data=f"answer_{i}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            direction_emoji = "🇬🇷→🇷🇺" if quiz_data['direction'] == 'GR→RU' else "🇷🇺→🇬🇷"

            await context.bot.send_message(
                chat_id=user.id,
                text=f"{direction_emoji} {quiz_data['direction']}\n\n❓ {quiz_data['question']}\n\nВыберите правильный ответ:",
                reply_markup=reply_markup
            )

    logger.info(f"User {user.id} answered {'correctly' if is_correct else 'incorrectly'}")


# Handlers to register in bot.py
def get_quiz_handlers():
    """Returns list of handlers to register."""
    return [
        CommandHandler("quiz", quiz_command),
        CommandHandler("quiz_session", quiz_session_command),
        CommandHandler("stop", stop_command),
        CallbackQueryHandler(answer_callback, pattern="^answer_"),
    ]
