# Phase 1: Infrastructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Set up project structure, database, configuration, and minimal bot initialization

**Architecture:** Clean layered architecture with database layer, service layer, and handlers. SQLite for data persistence, python-telegram-bot for Telegram API, python-dotenv for configuration.

**Tech Stack:** Python 3.10+, python-telegram-bot, SQLite, python-dotenv

---

## Task 1: Project Structure and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `database/__init__.py`
- Create: `handlers/__init__.py`
- Create: `services/__init__.py`
- Create: `utils/__init__.py`

**Step 1: Create requirements.txt**

```txt
python-telegram-bot==20.7
APScheduler==3.10.4
openpyxl==3.1.2
python-dotenv==1.0.0
```

**Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages installed successfully

**Step 3: Create package __init__.py files**

Run: `touch database/__init__.py handlers/__init__.py services/__init__.py utils/__init__.py`
Expected: Files created

**Step 4: Verify structure**

Run: `ls -R`
Expected: All directories with __init__.py visible

**Step 5: Commit**

```bash
git add requirements.txt database/ handlers/ services/ utils/
git commit -m "feat: add project structure and dependencies"
```

---

## Task 2: Configuration Module

**Files:**
- Create: `config.py`
- Modify: `.env.example`

**Step 1: Create config.py with environment loading**

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN must be set in .env file")

# Admin whitelist (Telegram usernames without @)
ADMIN_USERNAMES = os.getenv('ADMIN_USERNAME', '').split(',')

# Database
DATABASE_PATH = "database/words.db"

# Default settings
DEFAULT_QUESTIONS_PER_SESSION = 5
DEFAULT_SESSION_INTERVAL_MINUTES = 15
DEFAULT_GROUP_POST_INTERVAL_MINUTES = 30

# Quiz settings
MIN_ANSWERS_FOR_DIFFICULTY_CALC = 3
DIFFICULTY_MULTIPLIER_LOW = 0.5
DIFFICULTY_MULTIPLIER_NORMAL = 1.0
DIFFICULTY_MULTIPLIER_HIGH = 2.0
SUCCESS_RATE_THRESHOLD_HIGH = 0.9
SUCCESS_RATE_THRESHOLD_LOW = 0.7
```

**Step 2: Verify config loads without errors**

Run: `python -c "import config; print('Config loaded successfully')"`
Expected: Should fail with "BOT_TOKEN must be set" (this is correct behavior)

**Step 3: Create .env file for testing**

Create `.env` file (NOT committed):
```
BOT_TOKEN=test_token_placeholder
ADMIN_USERNAME=test_user
```

**Step 4: Verify config loads with .env**

Run: `python -c "import config; print(f'Token: {config.BOT_TOKEN[:10]}..., Admin: {config.ADMIN_USERNAMES}')"`
Expected: "Token: test_token..., Admin: ['test_user']"

**Step 5: Commit**

```bash
git add config.py
git commit -m "feat: add configuration module with environment variables"
```

---

## Task 3: Database Models

**Files:**
- Create: `database/models.py`

**Step 1: Create database schema definitions**

```python
"""
Database schema definitions for Greek Learning Bot.
Each function returns a CREATE TABLE SQL statement.
"""

def create_words_table():
    """Table for storing Greek words/phrases with Russian translations."""
    return """
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        greek TEXT NOT NULL,
        russian TEXT NOT NULL,
        word_type TEXT NOT NULL CHECK(word_type IN ('noun', 'verb', 'adjective', 'adverb', 'pronoun', 'preposition', 'conjunction', 'phrase')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    );
    """

def create_users_table():
    """Table for storing user preferences and settings."""
    return """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        quiz_session_active BOOLEAN DEFAULT 0,
        auto_quiz_enabled BOOLEAN DEFAULT 1,
        questions_per_session INTEGER DEFAULT 5,
        session_interval_minutes INTEGER DEFAULT 15,
        last_auto_quiz TIMESTAMP,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

def create_user_stats_table():
    """Table for tracking user performance on each word."""
    return """
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        word_id INTEGER NOT NULL,
        correct_answers INTEGER DEFAULT 0,
        total_answers INTEGER DEFAULT 0,
        last_asked TIMESTAMP,
        difficulty_multiplier REAL DEFAULT 1.0,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (word_id) REFERENCES words(id),
        UNIQUE(user_id, word_id)
    );
    """

def create_chat_contexts_table():
    """Table for storing group/topic configurations."""
    return """
    CREATE TABLE IF NOT EXISTS chat_contexts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        chat_type TEXT NOT NULL CHECK(chat_type IN ('private', 'group', 'supergroup')),
        topic_id INTEGER,
        enabled BOOLEAN DEFAULT 1,
        task_type TEXT CHECK(task_type IN ('conjugation', 'translation', 'vocabulary', 'custom')),
        schedule_interval_minutes INTEGER DEFAULT 30,
        last_posted TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(chat_id, topic_id)
    );
    """

def create_group_tasks_table():
    """Table for storing group task templates."""
    return """
    CREATE TABLE IF NOT EXISTS group_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_type TEXT NOT NULL,
        template TEXT NOT NULL,
        target_word_id INTEGER,
        correct_answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (target_word_id) REFERENCES words(id)
    );
    """

def create_admins_table():
    """Table for admin whitelist."""
    return """
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

def get_all_tables():
    """Returns list of all table creation functions."""
    return [
        create_words_table,
        create_users_table,
        create_user_stats_table,
        create_chat_contexts_table,
        create_group_tasks_table,
        create_admins_table
    ]
```

**Step 2: Verify models module imports**

Run: `python -c "from database.models import get_all_tables; print(f'Found {len(get_all_tables())} tables')"`
Expected: "Found 6 tables"

**Step 3: Commit**

```bash
git add database/models.py
git commit -m "feat: add database schema definitions"
```

---

## Task 4: Database Manager

**Files:**
- Create: `database/db.py`

**Step 1: Create database manager with connection and initialization**

```python
"""
Database manager for Greek Learning Bot.
Handles connection, initialization, and basic operations.
"""
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any

import config
from database.models import get_all_tables

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database connection and operations."""

    def __init__(self, db_path: str = None):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Uses config.DATABASE_PATH if not provided.
        """
        self.db_path = db_path or config.DATABASE_PATH
        self._connection = None

    @contextmanager
    def get_connection(self):
        """Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def initialize_database(self):
        """Create all tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create all tables
            for create_table_func in get_all_tables():
                sql = create_table_func()
                cursor.execute(sql)
                logger.info(f"Executed: {create_table_func.__name__}")

            logger.info("Database initialized successfully")

    def add_test_data(self):
        """Add test data for development."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Add test words
            test_words = [
                ('κάνω', 'делать', 'verb'),
                ('Καλημέρα', 'Доброе утро', 'phrase'),
                ('νερό', 'вода', 'noun'),
                ('καλός', 'хороший', 'adjective'),
                ('Ευχαριστώ', 'Спасибо', 'phrase'),
                ('σπίτι', 'дом', 'noun'),
                ('γρήγορα', 'быстро', 'adverb'),
                ('εγώ', 'я', 'pronoun'),
            ]

            cursor.executemany(
                'INSERT OR IGNORE INTO words (greek, russian, word_type) VALUES (?, ?, ?)',
                test_words
            )

            logger.info(f"Added {len(test_words)} test words")

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of rows as sqlite3.Row objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount


# Global database instance
db = DatabaseManager()
```

**Step 2: Test database initialization**

Create test script `test_db.py`:
```python
import logging
import os
from database.db import db

logging.basicConfig(level=logging.INFO)

# Clean up test database if exists
if os.path.exists('database/words.db'):
    os.remove('database/words.db')

# Initialize
db.initialize_database()
db.add_test_data()

# Verify
words = db.execute_query('SELECT * FROM words')
print(f"Test passed: Found {len(words)} words in database")
for word in words:
    print(f"  - {word['greek']} = {word['russian']} ({word['word_type']})")
```

**Step 3: Run test**

Run: `python test_db.py`
Expected: Should show 8 test words added successfully (verb, noun, adjective, adverb, pronoun, phrases)

**Step 4: Clean up test script**

Run: `rm test_db.py`

**Step 5: Commit**

```bash
git add database/db.py
git commit -m "feat: add database manager with initialization"
```

---

## Task 5: Bot Initialization

**Files:**
- Create: `bot.py`

**Step 1: Create minimal bot with /start command**

```python
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
```

**Step 2: Verify bot script has no syntax errors**

Run: `python -m py_compile bot.py`
Expected: No output (success)

**Step 3: Check if bot can import all dependencies**

Run: `python -c "import bot; print('Bot module loaded successfully')"`
Expected: "Bot module loaded successfully"

**Step 4: Commit**

```bash
git add bot.py
git commit -m "feat: add bot initialization with /start and /help commands"
```

---

## Task 6: Update README with Setup Instructions

**Files:**
- Modify: `README.md`

**Step 1: Add installation and setup instructions**

Replace README.md content with:

```markdown
# Greek Learning Telegram Bot

Telegram-бот для изучения греческого языка с автоматическими квизами, групповыми заданиями и адаптивным обучением.

## Статус проекта

🚧 **Phase 1 Complete** - Infrastructure ready, basic bot functional

## Возможности

- 📝 Квизы с множественным выбором (греческий ⇄ русский)
- 🤖 Автоматические квизы по расписанию
- 📊 Статистика и адаптивное обучение
- 👥 Групповые задания с постингом в топики
- 📥 Импорт/экспорт словаря (Excel/CSV/JSON)
- 🎯 Интерактивное добавление слов через команды

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ShurikGr/greek-learning-bot.git
cd greek-learning-bot
```

### 2. Создать виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте:
- `BOT_TOKEN` - получите токен у [@BotFather](https://t.me/BotFather)
- `ADMIN_USERNAME` - ваш Telegram username (без @)

### 5. Запустить бота

```bash
python bot.py
```

## Получение токена бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env` файл

## Структура проекта

```
greek-learning-bot/
├── bot.py                 # Точка входа
├── config.py             # Конфигурация
├── requirements.txt      # Зависимости
├── database/            # База данных
│   ├── db.py           # Менеджер БД
│   └── models.py       # Схемы таблиц
├── handlers/           # Обработчики команд (в разработке)
├── services/           # Бизнес-логика (в разработке)
└── utils/              # Утилиты (в разработке)
```

## Документация

- [Design Document](docs/plans/2026-01-30-greek-learning-bot-design.md) - Полный дизайн системы
- [Phase 1 Plan](docs/plans/2026-01-30-phase-1-infrastructure.md) - План реализации инфраструктуры

## Разработка

### Фазы реализации

- ✅ Phase 1: Infrastructure (Database, Config, Bot Init)
- 🔜 Phase 2: Quiz System
- 🔜 Phase 3: Admin Functions
- 🔜 Phase 4: Scheduler & Auto-quizzes
- 🔜 Phase 5: Group Tasks
- 🔜 Phase 6: Adaptive Learning
- 🔜 Phase 7: Polish & Testing
- 🔜 Phase 8: Deployment

## Технологии

- Python 3.10+
- python-telegram-bot 20.7
- SQLite
- APScheduler
- openpyxl

## Лицензия

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with installation instructions"
```

---

## Task 7: Verification and Testing

**Files:**
- None (verification only)

**Step 1: Verify all files exist**

Run: `ls -R`
Expected: Should see all created files in correct structure

**Step 2: Verify database can be initialized**

Run: `python -c "from database.db import db; db.initialize_database(); print('Database OK')"`
Expected: "Database OK"

**Step 3: Verify config loads correctly**

Run: `python -c "import config; print(f'Config OK - Token present: {bool(config.BOT_TOKEN)}')"`
Expected: "Config OK - Token present: True"

**Step 4: Check git status**

Run: `git status`
Expected: "nothing to commit, working tree clean"

**Step 5: View commit history**

Run: `git log --oneline`
Expected: Should show all 6 commits from this phase

---

## Summary

Phase 1 is complete when:
- ✅ Project structure created with all directories
- ✅ Dependencies installed (requirements.txt)
- ✅ Configuration module with environment variables
- ✅ Database schema defined (6 tables)
- ✅ Database manager with initialization
- ✅ Bot runs with /start and /help commands
- ✅ README updated with setup instructions
- ✅ All changes committed to git

**Next Phase:** Phase 2 - Quiz System (handlers/quiz.py, services/quiz_service.py)

**Estimated completion time:** 2-3 hours
