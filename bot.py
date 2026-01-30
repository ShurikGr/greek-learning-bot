"""
Greek Learning Telegram Bot
Main entry point and bot initialization.
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

import config
from database.db import db

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user

    await update.message.reply_text(
        f"Привет, {user.first_name}!\n\n"
        f"Я бот для изучения греческого языка.\n\n"
        f"Доступные команды:\n"
        f"/start - показать это сообщение\n"
        f"/help - полная справка\n\n"
        f"Функционал бота в разработке..."
    )

    logger.info(f"User {user.id} (@{user.username}) started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "📚 Greek Learning Bot - Справка\n\n"
        "Этот бот поможет вам учить греческий язык!\n\n"
        "Основные команды будут добавлены в следующих фазах разработки."
    )


def main():
    """Start the bot."""
    # Initialize database
    logger.info("Initializing database...")
    db.initialize_database()
    db.add_test_data()
    logger.info("Database ready")

    # Create application
    logger.info("Creating bot application...")
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Start bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
