"""
VaaniAI — AI-Powered Answer Evaluator
Uses Ollama to intelligently score interview answers instead of just counting words.
Falls back to keyword/length-based scoring if AI is unavailable.
"""

import requests
from app.config import OLLAMA_URL, FAST_AI_MODEL


class AnswerEvaluator:
    """
    Evaluates interview answers using AI + heuristics.
    
    Scoring dimensions:
        1. Relevance — Does the answer address the question?
        2. Depth — Is it detailed or surface-level?
        3. Clarity — Is it well-structured and clear?
        4. Technical Accuracy — Are technical terms used correctly?
    """

    def __init__(self):
        self.model = FAST_AI_MODEL
        self.url = OLLAMA_URL

    def evaluate(self, question: str, answer: str, topic: str = "general") -> dict:
        """
        Evaluate an answer and return a detailed scoring dict.
        
        Returns:
            {
                "score": float (1-10),
                "relevance": float (1-10),
                "depth": float (1-10),
                "clarity": float (1-10),
                "feedback": str,
                "grade": str (A/B/C/D/F)
            }
        """
        if not answer or len(answer.strip()) < 3:
            return {
                "score": 1.0,
                "relevance": 0.0,
                "depth": 0.0,
                "clarity": 0.0,
                "feedback": "No answer was provided.",
                "grade": "F",
            }

        # Try AI-based evaluation first
        ai_result = self._evaluate_with_ai(question, answer, topic)
        if ai_result:
            return ai_result

        # Fallback to heuristic evaluation
        return self._evaluate_heuristic(question, answer)

    def _evaluate_with_ai(self, question: str, answer: str, topic: str) -> dict | None:
        """Use Ollama to evaluate the answer intelligently."""
        try:
            prompt = (
                f"You are a JUDGE, not a candidate. Do NOT answer the question yourself.\n"
                f"EVALUATE this candidate's answer to an interview question.\n\n"
                f"Question asked: {question}\n"
                f"Candidate said: {answer}\n\n"
                f"Give a score from 1 to 10 and one short feedback sentence about the candidate's answer quality.\n"
                f"DO NOT answer the question. Only judge the candidate's response.\n"
                f"Reply in this EXACT format only:\n"
                f"SCORE: 7\n"
                f"FEEDBACK: The candidate gave a clear answer but could add more detail.\n"
            )

            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 50,
                    }
                },
                timeout=10
            )

            if response.status_code == 200:
                text = response.json().get("response", "")
                return self._parse_ai_response(text, question, answer)

        except Exception as e:
            print(f"[EVALUATOR] AI evaluation failed: {e}")

        return None

    def _parse_ai_response(self, text: str, question: str, answer: str) -> dict | None:
        """Parse the AI's structured response into a scoring dict."""
        try:
            score = 5.0
            feedback = "Average response."

            for line in text.strip().split("\n"):
                line = line.strip()
                if line.upper().startswith("SCORE:"):
                    score_str = line.split(":")[1].strip().split("/")[0].strip()
                    # Extract just the number
                    import re
                    nums = re.findall(r'[\d.]+', score_str)
                    if nums:
                        score = float(nums[0])
                        score = max(1.0, min(10.0, score))
                elif line.upper().startswith("FEEDBACK:"):
                    feedback = line.split(":", 1)[1].strip()
                    # Strip quotes that AI sometimes wraps around feedback
                    feedback = feedback.strip('"').strip("'").strip()

            # Calculate sub-scores from main score
            word_count = len(answer.split())
            relevance = min(score + 0.5, 10.0) if word_count > 5 else max(score - 1.0, 1.0)
            depth = min(score, 10.0) if word_count > 15 else max(score - 1.5, 1.0)
            clarity = score  # AI judges this implicitly

            return {
                "score": round(score, 1),
                "relevance": round(relevance, 1),
                "depth": round(depth, 1),
                "clarity": round(clarity, 1),
                "feedback": feedback,
                "grade": self._score_to_grade(score),
            }
        except Exception:
            return None

    def _evaluate_heuristic(self, question: str, answer: str) -> dict:
        """Fallback: heuristic scoring based on answer quality indicators."""
        words = answer.split()
        word_count = len(words)
        unique_words = len(set(w.lower() for w in words))

        # Base score from word count (but smarter than just counting)
        if word_count >= 40:
            base_score = 8.5
        elif word_count >= 25:
            base_score = 7.5
        elif word_count >= 15:
            base_score = 6.0
        elif word_count >= 8:
            base_score = 4.5
        elif word_count >= 3:
            base_score = 3.0
        else:
            base_score = 1.5

        # Bonus for vocabulary diversity (unique words ratio)
        diversity = unique_words / max(word_count, 1)
        if diversity > 0.7:
            base_score = min(base_score + 0.5, 10.0)

        # Bonus for question keywords appearing in answer (relevance)
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        overlap = len(q_words & a_words)
        relevance_bonus = min(overlap * 0.3, 1.0)
        relevance = min(base_score + relevance_bonus, 10.0)

        # Depth based on sentence count
        sentences = answer.count(".") + answer.count("!") + answer.count("?")
        depth = min(base_score + (sentences * 0.5), 10.0)

        feedback = self._generate_feedback(base_score, word_count)

        return {
            "score": round(base_score, 1),
            "relevance": round(relevance, 1),
            "depth": round(min(depth, 10.0), 1),
            "clarity": round(base_score, 1),
            "feedback": feedback,
            "grade": self._score_to_grade(base_score),
        }

    def _generate_feedback(self, score: float, word_count: int) -> str:
        """Generate human-readable feedback based on score."""
        if score >= 8.5:
            return "Excellent answer! Very detailed and well-explained."
        elif score >= 7.0:
            return "Good answer. Well-structured with relevant details."
        elif score >= 5.5:
            return "Decent answer, but could use more depth and examples."
        elif score >= 4.0:
            return "Answer is too brief. Try to explain with more detail."
        elif score >= 2.5:
            return "Very short answer. Please elaborate more on your points."
        return "Answer was too brief or unclear."

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 9.0:
            return "A+"
        elif score >= 8.0:
            return "A"
        elif score >= 7.0:
            return "B+"
        elif score >= 6.0:
            return "B"
        elif score >= 5.0:
            return "C"
        elif score >= 4.0:
            return "D"
        return "F"
