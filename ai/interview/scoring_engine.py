"""
VaaniAI — Scoring Engine
Provides aggregate scoring utilities for interview analysis.
Used by the report generator to compute final statistics.
"""


class ScoringEngine:
    """
    Computes aggregate interview statistics and performance metrics.
    """

    @staticmethod
    def compute_stats(scores: list[float]) -> dict:
        """
        Compute statistical summary of interview scores.
        
        Args:
            scores: List of per-question scores (1-10)
            
        Returns:
            Dict with average, min, max, passed count, etc.
        """
        if not scores:
            return {
                "average": 0.0,
                "min_score": 0.0,
                "max_score": 0.0,
                "total_questions": 0,
                "passed_count": 0,
                "failed_count": 0,
                "pass_rate": 0.0,
                "grade": "F",
                "consistency": 0.0,
            }

        avg = sum(scores) / len(scores)
        passed = sum(1 for s in scores if s >= 5.0)
        failed = len(scores) - passed

        # Consistency = how uniform are the scores (lower variance = more consistent)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        consistency = max(0.0, 10.0 - variance)  # 10 = perfectly consistent

        return {
            "average": round(avg, 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "total_questions": len(scores),
            "passed_count": passed,
            "failed_count": failed,
            "pass_rate": round((passed / len(scores)) * 100, 1),
            "grade": ScoringEngine.score_to_grade(avg),
            "consistency": round(consistency, 2),
        }

    @staticmethod
    def score_to_grade(score: float) -> str:
        """Convert numeric score (1-10) to letter grade."""
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

    @staticmethod
    def get_performance_summary(avg_score: float) -> str:
        """Generate a human-readable performance summary."""
        if avg_score >= 8.5:
            return "Outstanding candidate. Demonstrated exceptional knowledge and communication skills."
        elif avg_score >= 7.0:
            return "Strong candidate. Shows good understanding with minor areas for growth."
        elif avg_score >= 5.5:
            return "Average candidate. Needs to develop deeper understanding and provide more detailed responses."
        elif avg_score >= 4.0:
            return "Below average. Candidate requires more preparation and practice."
        return "Needs significant improvement in fundamentals and interview skills."
