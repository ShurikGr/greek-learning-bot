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
