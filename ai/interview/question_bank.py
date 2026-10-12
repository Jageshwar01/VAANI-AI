"""
VaaniAI — Question Bank
Organized question sets by interview type with difficulty levels.
Supports loading custom questions from data/question_sets/ directory.
"""

import os
import random
from app.config import QUESTION_SETS_DIR


class QuestionBank:
    """
    Professional interview question bank with multiple categories.
    
    Structure:
        Each question is a dict: {"q": "...", "topic": "...", "difficulty": "easy|medium|hard"}
    """

    # ── Built-in Question Sets ──────────────────────────────────────────────

    GENERAL = [
        {"q": "Please introduce yourself briefly.", "topic": "introduction", "difficulty": "easy"},
        {"q": "What are your strengths and weaknesses?", "topic": "personality", "difficulty": "easy"},
        {"q": "Where do you see yourself in five years?", "topic": "career", "difficulty": "medium"},
        {"q": "Why should we hire you?", "topic": "motivation", "difficulty": "medium"},
        {"q": "Tell me about a challenge you faced and how you solved it.", "topic": "problem_solving", "difficulty": "hard"},
    ]

    PYTHON = [
        {"q": "What is Python, and why is it popular?", "topic": "basics", "difficulty": "easy"},
        {"q": "What is the difference between a list and a tuple in Python?", "topic": "data_structures", "difficulty": "easy"},
        {"q": "Explain the concept of object oriented programming.", "topic": "oop", "difficulty": "medium"},
        {"q": "What are decorators in Python? Give a simple example.", "topic": "advanced", "difficulty": "medium"},
        {"q": "Explain the difference between shallow copy and deep copy.", "topic": "advanced", "difficulty": "hard"},
        {"q": "What is a generator, and how is it different from a normal function?", "topic": "advanced", "difficulty": "hard"},
    ]

    WEB_DEV = [
        {"q": "What is the difference between HTML, CSS, and JavaScript?", "topic": "basics", "difficulty": "easy"},
        {"q": "Explain what a REST API is.", "topic": "api", "difficulty": "medium"},
        {"q": "What is the difference between GET and POST requests?", "topic": "http", "difficulty": "easy"},
        {"q": "What is responsive web design?", "topic": "css", "difficulty": "medium"},
        {"q": "Explain the concept of a database and why it is important.", "topic": "database", "difficulty": "medium"},
    ]

    DATA_SCIENCE = [
        {"q": "What is the difference between supervised and unsupervised learning?", "topic": "ml_basics", "difficulty": "easy"},
        {"q": "What is overfitting, and how can you prevent it?", "topic": "ml_concepts", "difficulty": "medium"},
        {"q": "Explain the difference between classification and regression.", "topic": "ml_basics", "difficulty": "easy"},
        {"q": "What is a neural network? Explain in simple terms.", "topic": "deep_learning", "difficulty": "medium"},
        {"q": "What are the steps involved in a typical data science project?", "topic": "workflow", "difficulty": "hard"},
    ]

    HR = [
        {"q": "Tell me about yourself.", "topic": "introduction", "difficulty": "easy"},
        {"q": "What motivates you to do your best work?", "topic": "motivation", "difficulty": "easy"},
        {"q": "How do you handle pressure and stressful situations?", "topic": "stress", "difficulty": "medium"},
        {"q": "Describe a situation where you worked effectively in a team.", "topic": "teamwork", "difficulty": "medium"},
        {"q": "What are your salary expectations?", "topic": "negotiation", "difficulty": "hard"},
        {"q": "Do you have any questions for us?", "topic": "closing", "difficulty": "easy"},
    ]

    # Map of type names to question lists
    CATEGORIES = {
        "general": GENERAL,
        "python": PYTHON,
        "web": WEB_DEV,
        "data_science": DATA_SCIENCE,
        "hr": HR,
    }

    def __init__(self):
        self.custom_questions = {}
        self._load_custom_sets()

    def _load_custom_sets(self):
        """Load custom question sets from data/question_sets/ directory."""
        if not os.path.exists(QUESTION_SETS_DIR):
            return

        for filename in os.listdir(QUESTION_SETS_DIR):
            if filename.endswith(".txt"):
                category = filename.replace(".txt", "").lower()
                filepath = os.path.join(QUESTION_SETS_DIR, filename)
                questions = []
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                questions.append({
                                    "q": line,
                                    "topic": "custom",
                                    "difficulty": "medium",
                                })
                    if questions:
                        self.custom_questions[category] = questions
                        print(f"[QUESTION_BANK] Loaded {len(questions)} custom questions from {filename}")
                except Exception as e:
                    print(f"[QUESTION_BANK] Error loading {filename}: {e}")

    def get_questions(self, interview_type: str = "general", max_questions: int = 5) -> list[dict]:
        """
        Get questions for a specific interview type.
        Selects a mix of easy, medium, and hard questions.
        """
        # Check custom sets first, then built-in
        if interview_type in self.custom_questions:
            pool = self.custom_questions[interview_type]
        elif interview_type in self.CATEGORIES:
            pool = self.CATEGORIES[interview_type]
        else:
            pool = self.GENERAL

        # If pool is smaller than requested, return all
        if len(pool) <= max_questions:
            return pool.copy()

        # Smart selection: mix of difficulties
        easy = [q for q in pool if q["difficulty"] == "easy"]
        medium = [q for q in pool if q["difficulty"] == "medium"]
        hard = [q for q in pool if q["difficulty"] == "hard"]

        selected = []
        # Start with 1 easy, then medium, then hard
        if easy:
            selected.append(random.choice(easy))
        for q in random.sample(medium, min(len(medium), max_questions - 2)):
            selected.append(q)
        if hard and len(selected) < max_questions:
            selected.append(random.choice(hard))

        # Fill remaining with random from pool
        remaining = [q for q in pool if q not in selected]
        while len(selected) < max_questions and remaining:
            selected.append(remaining.pop(random.randint(0, len(remaining) - 1)))

        return selected[:max_questions]

    def get_default_questions(self) -> list[str]:
        """Backward compatible — returns just question strings."""
        return [q["q"] for q in self.get_questions("general", 5)]

    def get_available_types(self) -> list[str]:
        """Return all available interview types."""
        types = list(self.CATEGORIES.keys())
        types.extend(self.custom_questions.keys())
        return list(set(types))