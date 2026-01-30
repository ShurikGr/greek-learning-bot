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
