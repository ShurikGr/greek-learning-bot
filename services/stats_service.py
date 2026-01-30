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
