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
