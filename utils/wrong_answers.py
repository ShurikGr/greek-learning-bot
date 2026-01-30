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
