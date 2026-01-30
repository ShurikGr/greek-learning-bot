# Greek Learning Bot - Complete Implementation Guide

**Version:** 1.0
**Last Updated:** 2026-01-30
**Status:** Ready for Implementation

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Overview](#project-overview)
3. [Architecture](#architecture)
4. [Database Schema](#database-schema)
5. [Configuration](#configuration)
6. [All Bot Commands](#all-bot-commands)
7. [Phase 1: Infrastructure](#phase-1-infrastructure)
8. [Phase 2: Quiz System](#phase-2-quiz-system)
9. [Phase 3: Admin Functions](#phase-3-admin-functions)
10. [Phase 4: Scheduler & Auto-quizzes](#phase-4-scheduler--auto-quizzes)
11. [Phase 5: Group Tasks](#phase-5-group-tasks)
12. [Phase 6: Adaptive Learning](#phase-6-adaptive-learning)
13. [Phase 7: Polish & Testing](#phase-7-polish--testing)
14. [Phase 8: Deployment](#phase-8-deployment)
15. [Code Templates](#code-templates)
16. [Testing Checklist](#testing-checklist)
17. [Working with PDF Sources](#working-with-pdf-sources)

---

## Quick Start

**To resume development in a new session:**

1. Read this entire guide
2. Check current project state: `git log --oneline`
3. Identify which phase is next (see Phase status in each section)
4. Follow step-by-step instructions for that phase
5. Test after each task
6. Commit frequently

**Current Status:**
- ✅ Phase 1: Complete (Infrastructure ready)
- 🔜 Phase 2: Not started (Quiz System)

---

## Project Overview

**Goal:** Telegram bot for learning Greek language with adaptive quizzes, group tasks, and progress tracking.

**Key Features:**
- Quiz system with multiple choice (Greek ⇄ Russian)
- Automatic scheduled quizzes
- Adaptive learning (difficult words shown more often)
- Group task posting to Telegram groups/topics
- Import/Export vocabulary (Excel/CSV/JSON)
- PDF processing from teacher materials
- Statistics and progress tracking

**Tech Stack:**
- Python 3.10+
- python-telegram-bot 20.7
- SQLite
- APScheduler
- openpyxl

---

## Architecture

### Project Structure

```
greek-learning-bot/
├── bot.py                 # Entry point
├── config.py              # Configuration
├── requirements.txt       # Dependencies
│
├── data/                  # Data files (NOT in git)
│   ├── source/           # PDF/DOCX from teacher
│   └── processed/        # Excel files ready for import
│
├── database/
│   ├── db.py             # Database manager
│   ├── models.py         # Table schemas
│   └── words.db          # SQLite database (NOT in git)
│
├── handlers/
│   ├── admin.py          # /add, /import, /export
│   ├── quiz.py           # /quiz, /quiz_session, /stop
│   ├── group.py          # /setup, /add_task
│   └── stats.py          # /stats, /difficult, /progress
│
├── services/
│   ├── quiz_service.py       # Quiz generation logic
│   ├── scheduler_service.py  # Cron jobs
│   ├── stats_service.py      # Statistics & adaptivity
│   └── task_service.py       # Group task posting
│
├── utils/
│   ├── wrong_answers.py      # Generate wrong answers
│   ├── import_export.py      # File import/export
│   └── validators.py         # Data validation
│
└── docs/
    ├── IMPLEMENTATION_GUIDE.md  # This file
    └── plans/                   # Design docs
```

### Architectural Principles

1. **Layered Architecture:**
   - Handlers: User interaction, command processing
   - Services: Business logic
   - Database: Data persistence
   - Utils: Helper functions

2. **Single Responsibility:**
   - Each module has one clear purpose
   - Easy to test and maintain

3. **DRY, YAGNI, TDD:**
   - Don't Repeat Yourself
   - You Ain't Gonna Need It
   - Test-Driven Development (optional for MVP)

---

## Database Schema

### Table: `words`

Stores Greek words/phrases with Russian translations.

```sql
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    greek TEXT NOT NULL,
    russian TEXT NOT NULL,
    word_type TEXT NOT NULL CHECK(word_type IN (
        'noun',        -- существительное
        'verb',        -- глагол
        'adjective',   -- прилагательное
        'adverb',      -- наречие
        'pronoun',     -- местоимение
        'preposition', -- предлог
        'conjunction', -- союз
        'phrase'       -- фраза
    )),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER  -- Telegram user_id of admin
);
```

### Table: `users`

Stores user preferences and settings.

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,  -- Telegram user_id
    username TEXT,
    first_name TEXT,
    quiz_session_active BOOLEAN DEFAULT 0,
    auto_quiz_enabled BOOLEAN DEFAULT 1,
    questions_per_session INTEGER DEFAULT 5,
    session_interval_minutes INTEGER DEFAULT 15,
    last_auto_quiz TIMESTAMP,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: `user_stats`

Tracks user performance on each word for adaptive learning.

```sql
CREATE TABLE user_stats (
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
```

### Table: `chat_contexts`

Stores configuration for groups/topics.

```sql
CREATE TABLE chat_contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    chat_type TEXT NOT NULL CHECK(chat_type IN ('private', 'group', 'supergroup')),
    topic_id INTEGER,  -- NULL if not a topic
    enabled BOOLEAN DEFAULT 1,
    task_type TEXT CHECK(task_type IN ('conjugation', 'translation', 'vocabulary', 'custom')),
    schedule_interval_minutes INTEGER DEFAULT 30,
    last_posted TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, topic_id)
);
```

### Table: `group_tasks`

Templates for group tasks.

```sql
CREATE TABLE group_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    template TEXT NOT NULL,  -- e.g., "Conjugate verb {word}"
    target_word_id INTEGER,  -- NULL if not tied to specific word
    correct_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (target_word_id) REFERENCES words(id)
);
```

### Table: `admins`

Admin whitelist.

```sql
CREATE TABLE admins (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Configuration

### Environment Variables (.env)

```bash
# Required
BOT_TOKEN=your_telegram_bot_token_from_botfather

# Admin usernames (comma-separated, without @)
ADMIN_USERNAME=your_username,another_admin
```

### Config Constants (config.py)

```python
# Database
DATABASE_PATH = "database/words.db"

# Default quiz settings
DEFAULT_QUESTIONS_PER_SESSION = 5
DEFAULT_SESSION_INTERVAL_MINUTES = 15
DEFAULT_GROUP_POST_INTERVAL_MINUTES = 30

# Adaptive learning thresholds
MIN_ANSWERS_FOR_DIFFICULTY_CALC = 3
DIFFICULTY_MULTIPLIER_LOW = 0.5      # Easy words (>90% correct)
DIFFICULTY_MULTIPLIER_NORMAL = 1.0   # Normal words
DIFFICULTY_MULTIPLIER_HIGH = 2.0     # Difficult words (<70% correct)
SUCCESS_RATE_THRESHOLD_HIGH = 0.9
SUCCESS_RATE_THRESHOLD_LOW = 0.7
```

---

## All Bot Commands

### User Commands (Private Chat)

**Quiz Commands:**
- `/quiz` - Get single quiz question
- `/quiz_session` - Start continuous quiz session
- `/stop` - Stop current quiz session

**Settings:**
- `/settings` - Configure auto-quizzes (interval, questions count)
- `/auto_on` - Enable automatic quizzes
- `/auto_off` - Disable automatic quizzes

**Statistics:**
- `/stats` - Show overall statistics (correct/total, success rate)
- `/difficult` - List difficult words for review
- `/progress` - Show progress over last week

**General:**
- `/start` - Welcome message, brief instructions
- `/help` - Complete command reference

### Admin Commands (Whitelist Only)

**Vocabulary Management:**
- `/add` - Add word/phrase interactively (dialog)
- `/import` - Import from Excel/CSV/JSON file
- `/export` - Export vocabulary to Excel
- `/template` - Get empty Excel template

**Task Management:**
- `/add_task` - Add task template for groups
- `/list_tasks` - List all available tasks

**Group Configuration:**
- `/setup` - Configure bot in group/topic (run in group)

---

## Phase 1: Infrastructure

**Status:** ✅ Complete
**Files:** `requirements.txt`, `config.py`, `database/models.py`, `database/db.py`, `bot.py`

### What Was Built:

1. ✅ Project structure with all directories
2. ✅ Dependencies (requirements.txt)
3. ✅ Configuration module (config.py)
4. ✅ Database schema (6 tables)
5. ✅ Database manager (db.py)
6. ✅ Bot initialization with /start and /help
7. ✅ README with setup instructions

### Verification:

```bash
# Check structure
ls -R

# Test database
python -c "from database.db import db; db.initialize_database(); print('DB OK')"

# Test config
python -c "import config; print('Config OK')"

# Check git commits
git log --oneline
```

---

## Phase 2: Quiz System

**Status:** 🔜 Not Started
**Estimated Time:** 4-5 hours

### Goals:

1. Implement quiz service (word selection, answer generation)
2. Create wrong answer generator
3. Add /quiz command (single question)
4. Add /quiz_session command (continuous session)
5. Record statistics to database

### Task 2.1: Wrong Answers Generator

**File:** `utils/wrong_answers.py`

```python
"""
Generate wrong answers for quiz questions.
"""
import random
from typing import List
from database.db import db


def generate_wrong_answers_for_word(correct_word_id: int, word_type: str, count: int = 3) -> List[str]:
    """
    Generate wrong answers by selecting random words of the same type.

    Args:
        correct_word_id: ID of the correct word
        word_type: Type of word (noun, verb, etc.)
        count: Number of wrong answers needed

    Returns:
        List of wrong answer translations
    """
    query = """
        SELECT russian FROM words
        WHERE id != ? AND word_type = ?
        ORDER BY RANDOM()
        LIMIT ?
    """
    results = db.execute_query(query, (correct_word_id, word_type, count))
    return [row['russian'] for row in results]


def generate_wrong_answers_for_phrase(correct_phrase: str, count: int = 3) -> List[str]:
    """
    Generate wrong answers for phrases.
    For MVP: Select random other phrases.
    Future: Use LLM to generate similar but wrong phrases.

    Args:
        correct_phrase: The correct phrase
        count: Number of wrong answers needed

    Returns:
        List of wrong answer translations
    """
    query = """
        SELECT russian FROM words
        WHERE russian != ? AND word_type = 'phrase'
        ORDER BY RANDOM()
        LIMIT ?
    """
    results = db.execute_query(query, (correct_phrase, count))
    return [row['russian'] for row in results]


def generate_wrong_answers(word_id: int, word_type: str, correct_answer: str, count: int = 3) -> List[str]:
    """
    Main function to generate wrong answers based on word type.

    Args:
        word_id: ID of the correct word
        word_type: Type (noun, verb, phrase, etc.)
        correct_answer: The correct translation
        count: Number of wrong answers needed

    Returns:
        List of wrong answers
    """
    if word_type == 'phrase':
        return generate_wrong_answers_for_phrase(correct_answer, count)
    else:
        return generate_wrong_answers_for_word(word_id, word_type, count)
```

**Steps:**
1. Create `utils/wrong_answers.py` with above code
2. Test: `python -c "from utils.wrong_answers import generate_wrong_answers; print('OK')"`
3. Commit: `git commit -m "feat: add wrong answer generator"`

### Task 2.2: Quiz Service

**File:** `services/quiz_service.py`

```python
"""
Quiz generation and management service.
"""
import random
from typing import Dict, List, Optional
from datetime import datetime
from database.db import db
from utils.wrong_answers import generate_wrong_answers


class QuizService:
    """Handles quiz generation and answer checking."""

    def select_random_word(self, user_id: Optional[int] = None) -> Optional[Dict]:
        """
        Select a random word for quiz.
        TODO Phase 6: Add adaptive selection based on user_stats.

        Args:
            user_id: User ID for adaptive selection (not used in Phase 2)

        Returns:
            Dictionary with word data or None if no words available
        """
        query = "SELECT * FROM words ORDER BY RANDOM() LIMIT 1"
        results = db.execute_query(query)

        if not results:
            return None

        row = results[0]
        return {
            'id': row['id'],
            'greek': row['greek'],
            'russian': row['russian'],
            'word_type': row['word_type']
        }

    def generate_quiz(self, user_id: Optional[int] = None) -> Optional[Dict]:
        """
        Generate a complete quiz question with 4 answer options.
        Alternates between GR→RU and RU→GR formats.

        Args:
            user_id: User ID for adaptive selection

        Returns:
            Dictionary with quiz data or None if not enough words
        """
        word = self.select_random_word(user_id)
        if not word:
            return None

        # Generate wrong answers
        wrong_answers = generate_wrong_answers(
            word['id'],
            word['word_type'],
            word['russian'],
            count=3
        )

        if len(wrong_answers) < 3:
            # Not enough words in database for quiz
            return None

        # Randomly choose quiz direction: GR→RU or RU→GR
        is_greek_to_russian = random.choice([True, False])

        if is_greek_to_russian:
            question = word['greek']
            correct_answer = word['russian']
        else:
            question = word['russian']
            correct_answer = word['greek']
            # For RU→GR, get wrong Greek words
            query = """
                SELECT greek FROM words
                WHERE id != ? AND word_type = ?
                ORDER BY RANDOM()
                LIMIT 3
            """
            results = db.execute_query(query, (word['id'], word['word_type']))
            wrong_answers = [row['greek'] for row in results]

        # Combine and shuffle answers
        all_answers = [correct_answer] + wrong_answers
        random.shuffle(all_answers)

        # Find correct answer index after shuffle
        correct_index = all_answers.index(correct_answer)

        return {
            'word_id': word['id'],
            'question': question,
            'answers': all_answers,
            'correct_index': correct_index,
            'direction': 'GR→RU' if is_greek_to_russian else 'RU→GR',
            'word_type': word['word_type']
        }

    def check_answer(self, quiz_data: Dict, user_answer_index: int) -> bool:
        """
        Check if user's answer is correct.

        Args:
            quiz_data: Quiz data from generate_quiz()
            user_answer_index: Index of answer user selected (0-3)

        Returns:
            True if correct, False otherwise
        """
        return user_answer_index == quiz_data['correct_index']


# Global quiz service instance
quiz_service = QuizService()
```

**Steps:**
1. Create `services/quiz_service.py` with above code
2. Test: `python -c "from services.quiz_service import quiz_service; q = quiz_service.generate_quiz(); print(q)"`
3. Commit: `git commit -m "feat: add quiz service with question generation"`

### Task 2.3: Stats Service (Basic)

**File:** `services/stats_service.py`

```python
"""
Statistics tracking service.
"""
from datetime import datetime
from typing import Optional, Dict
from database.db import db
import config


class StatsService:
    """Handles user statistics and progress tracking."""

    def record_answer(self, user_id: int, word_id: int, is_correct: bool):
        """
        Record user's answer to a quiz question.

        Args:
            user_id: Telegram user ID
            word_id: ID of the word
            is_correct: Whether answer was correct
        """
        # Check if stat entry exists
        query = "SELECT * FROM user_stats WHERE user_id = ? AND word_id = ?"
        results = db.execute_query(query, (user_id, word_id))

        if results:
            # Update existing stat
            stat = results[0]
            new_correct = stat['correct_answers'] + (1 if is_correct else 0)
            new_total = stat['total_answers'] + 1

            update_query = """
                UPDATE user_stats
                SET correct_answers = ?, total_answers = ?, last_asked = ?
                WHERE user_id = ? AND word_id = ?
            """
            db.execute_update(
                update_query,
                (new_correct, new_total, datetime.now(), user_id, word_id)
            )
        else:
            # Insert new stat
            insert_query = """
                INSERT INTO user_stats (user_id, word_id, correct_answers, total_answers, last_asked)
                VALUES (?, ?, ?, ?, ?)
            """
            db.execute_update(
                insert_query,
                (user_id, word_id, 1 if is_correct else 0, 1, datetime.now())
            )

    def get_user_stats(self, user_id: int) -> Dict:
        """
        Get overall statistics for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Dictionary with statistics
        """
        query = """
            SELECT
                SUM(correct_answers) as total_correct,
                SUM(total_answers) as total_questions
            FROM user_stats
            WHERE user_id = ?
        """
        results = db.execute_query(query, (user_id,))

        if not results or results[0]['total_questions'] is None:
            return {
                'total_correct': 0,
                'total_questions': 0,
                'success_rate': 0.0
            }

        total_correct = results[0]['total_correct']
        total_questions = results[0]['total_questions']
        success_rate = (total_correct / total_questions * 100) if total_questions > 0 else 0.0

        return {
            'total_correct': total_correct,
            'total_questions': total_questions,
            'success_rate': round(success_rate, 1)
        }


# Global stats service instance
stats_service = StatsService()
```

**Steps:**
1. Create `services/stats_service.py`
2. Test: `python -c "from services.stats_service import stats_service; print('OK')"`
3. Commit: `git commit -m "feat: add stats service for tracking answers"`

### Task 2.4: Quiz Handler (/quiz command)

**File:** `handlers/quiz.py`

```python
"""
Quiz command handlers.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from services.quiz_service import quiz_service
from services.stats_service import stats_service

logger = logging.getLogger(__name__)

# Conversation states
ANSWERING = 1


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

    logger.info(f"User {user.id} answered {'correctly' if is_correct else 'incorrectly'}")


# Handlers to register in bot.py
def get_quiz_handlers():
    """Returns list of handlers to register."""
    return [
        CommandHandler("quiz", quiz_command),
        CallbackQueryHandler(answer_callback, pattern="^answer_"),
    ]
```

**Steps:**
1. Create `handlers/quiz.py`
2. Update `bot.py` to register handlers:
   ```python
   from handlers.quiz import get_quiz_handlers

   # In main():
   for handler in get_quiz_handlers():
       application.add_handler(handler)
   ```
3. Test with real bot:
   - Run `python bot.py`
   - Send `/quiz` in Telegram
   - Answer question
   - Check stats recorded in database
4. Commit: `git commit -m "feat: add /quiz command with answer checking"`

### Task 2.5: Quiz Session (/quiz_session)

Add to `handlers/quiz.py`:

```python
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


# Update answer_callback to auto-send next question in session
async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... existing code ...

    await query.edit_message_text(response)
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


# Update get_quiz_handlers
def get_quiz_handlers():
    return [
        CommandHandler("quiz", quiz_command),
        CommandHandler("quiz_session", quiz_session_command),
        CommandHandler("stop", stop_command),
        CallbackQueryHandler(answer_callback, pattern="^answer_"),
    ]
```

**Steps:**
1. Add functions to `handlers/quiz.py`
2. Add import: `from database.db import db`
3. Test:
   - `/quiz_session` - starts session
   - Answer questions - auto-sends next
   - `/stop` - ends session
4. Commit: `git commit -m "feat: add /quiz_session continuous quiz mode"`

### Phase 2 Complete!

**Verify:**
- ✅ `/quiz` command works
- ✅ Answers are checked correctly
- ✅ Statistics recorded in database
- ✅ `/quiz_session` starts continuous mode
- ✅ `/stop` ends session

**Next:** Phase 3 - Admin Functions

---

## Phase 3: Admin Functions

**Status:** 🔜 Not Started
**Estimated Time:** 3-4 hours

[Content for Phase 3 would go here - /add command, /import, /export, etc.]

---

## Working with PDF Sources

### Directory Structure

- `data/source/` - Place PDF/DOCX files from teacher here
- `data/processed/` - Claude creates Excel files here ready for import

### Workflow

1. **Place PDF in data/source/**
   ```
   data/source/lesson-1-vocabulary.pdf
   ```

2. **Tell Claude to extract words:**
   > "Extract words from data/source/lesson-1-vocabulary.pdf and create Excel in data/processed/"

3. **Claude will:**
   - Read PDF using Read tool
   - Extract Greek words and Russian translations
   - Detect word types (verb, noun, etc.)
   - Create `data/processed/lesson-1-vocabulary.xlsx`

4. **Review and correct:**
   - Open Excel file
   - Check word types are correct
   - Fix any OCR errors
   - Save file

5. **Import to bot:**
   - Run bot: `python bot.py`
   - Send `/import` command
   - Attach the Excel file
   - Bot imports all words to database

### Example Excel Format

| Greek      | Russian        | Type        |
|------------|----------------|-------------|
| κάνω       | делать         | verb        |
| νερό       | вода           | noun        |
| καλός      | хороший        | adjective   |

---

## Testing Checklist

### Phase 1: Infrastructure
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `.env` file created with BOT_TOKEN
- [ ] `python bot.py` starts without errors
- [ ] `/start` command works in Telegram
- [ ] `/help` command works
- [ ] Database file created at `database/words.db`
- [ ] Test words visible in database

### Phase 2: Quiz System
- [ ] `/quiz` sends question with 4 answers
- [ ] Correct answer marked as correct
- [ ] Wrong answer shows correct answer
- [ ] Statistics updated after each answer
- [ ] `/quiz_session` starts continuous mode
- [ ] Questions auto-send in session mode
- [ ] `/stop` ends session and shows stats

### Phase 3-8: [To be added]

---

## Code Templates

### Adding New Command Handler

```python
# In handlers/your_handler.py
async def your_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /your_command."""
    user = update.effective_user

    # Your logic here

    await update.message.reply_text("Response")

# In bot.py
from handlers.your_handler import your_command
application.add_handler(CommandHandler("your_command", your_command))
```

### Database Query Pattern

```python
from database.db import db

# SELECT
results = db.execute_query("SELECT * FROM words WHERE id = ?", (word_id,))

# INSERT/UPDATE/DELETE
rows_affected = db.execute_update(
    "INSERT INTO words (greek, russian, word_type) VALUES (?, ?, ?)",
    (greek, russian, word_type)
)
```

### ConversationHandler Pattern

```python
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

STATE_1, STATE_2 = range(2)

async def start(update, context):
    await update.message.reply_text("Question 1?")
    return STATE_1

async def state_1(update, context):
    context.user_data['answer1'] = update.message.text
    await update.message.reply_text("Question 2?")
    return STATE_2

async def state_2(update, context):
    context.user_data['answer2'] = update.message.text
    # Process data
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        STATE_1: [MessageHandler(filters.TEXT, state_1)],
        STATE_2: [MessageHandler(filters.TEXT, state_2)],
    },
    fallbacks=[],
)
```

---

## End of Implementation Guide

**Remember:**
- Read relevant phase before starting
- Test after each task
- Commit frequently with clear messages
- Ask for clarification if anything unclear

**To resume in new session:**
1. Read this guide
2. Check `git log` for current state
3. Find next incomplete phase
4. Follow step-by-step instructions

Good luck! 🚀
