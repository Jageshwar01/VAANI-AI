"""
VaaniAI — Interview Manager
Conducts professional interviews with AI-powered evaluation,
real-time feedback, and automated report generation.

Designed to feel like a real interview experience:
  - Professional introduction and instructions
  - Patient listening with encouragement
  - Short-answer elaboration prompts
  - AI-powered answer evaluation (not just word counting)
  - Per-question verbal feedback
  - Professional report saved to data/reports/
"""

import time
import random
from datetime import datetime

from ai.interview.question_bank import QuestionBank
from ai.interview.answer_evaluator import AnswerEvaluator
from ai.interview.report_generator import ReportGenerator


class InterviewManager:
    def __init__(self, tts, stt, db, serial_bridge=None):
        self.tts = tts
        self.stt = stt
        self.db = db
        self.serial_bridge = serial_bridge
        self.question_bank = QuestionBank()
        self.evaluator = AnswerEvaluator()
        self.report_generator = ReportGenerator()

        # Encouragement phrases — rotate randomly so robot sounds natural
        self._encourage_phrases = [
            "Take your time. I am listening.",
            "Please go ahead with your answer.",
            "Do not worry, speak naturally.",
            "I am still here. Please continue.",
            "You can answer in your own words.",
        ]

        # Short-answer follow-up prompts
        self._elaborate_phrases = [
            "Could you elaborate a little more on that?",
            "Interesting. Can you explain further?",
            "That is a good start. Can you add more detail?",
        ]

        # Transition phrases between questions
        self._transition_phrases = [
            "Alright, let us move to the next question.",
            "Okay, here comes the next one.",
            "Good. Now let me ask you another question.",
            "Let us continue.",
        ]

    # ── Micro-Animations (subtle, interviewer-like) ───────────────────────

    def _nod(self):
        """Small head nod — shows the robot is listening/acknowledging."""
        if self.serial_bridge:
            self.serial_bridge.send("HEAD_LEFT")
            time.sleep(0.3)
            self.serial_bridge.send("HEAD_RIGHT")
            time.sleep(0.3)
            self.serial_bridge.send("HEAD_STOP")

    def _look_center(self):
        """Reset head to center — attentive posture before asking."""
        if self.serial_bridge:
            self.serial_bridge.send("HEAD_STOP")

    def _speak(self, text: str):
        """
        Safe speak: mute STT → speak → unmute STT.
        Used throughout interview to avoid TTS echo pickup.
        """
        print(f"VaaniAI: {text}")
        self.stt.mute()
        self.tts.speak(text, serial_bridge=self.serial_bridge)
        self.stt.unmute()
        time.sleep(0.3)  # Mic settle time after TTS

    def start_interview(self, candidate_name="Unknown Candidate", interview_type="general"):
        """
        Main interview flow:
        1. Introduction & instructions
        2. Ask interview type (if not specified)
        3. Ask questions with patient listening
        4. AI-evaluate each answer
        5. Give verbal feedback per question
        6. Summarize results
        7. Generate and save report
        """
        start_time = datetime.now().isoformat()

        # ── Save interview record to database ──────────────────────────────
        cursor = self.db.execute("""
            INSERT INTO interviews (candidate_name, interview_type, start_time, status)
            VALUES (?, ?, ?, ?)
        """, (candidate_name, interview_type, start_time, "started"))

        interview_id = cursor.lastrowid

        # ── Professional Introduction ──────────────────────────────────────
        self._speak(f"Hello {candidate_name}. Welcome to your interview.")
        self._speak("I will be your interviewer today. I am VaaniAI, an AI-powered interview assistant.")
        self._speak("I will ask you some questions. Please answer clearly and take your time.")
        self._speak("After each question, I will give you brief feedback.")

        # ── Ask interview type if generic ──────────────────────────────────
        if interview_type == "general":
            available = self.question_bank.get_available_types()
            self._speak(f"What type of interview would you like? I have: {', '.join(available)}.")
            self._speak("Just say the category name, or say general for a mix.")

            type_answer = None
            for _ in range(100):
                type_answer = self.stt.get_command()
                if type_answer:
                    break
                time.sleep(0.1)

            if type_answer:
                type_lower = type_answer.lower().strip()
                # Fuzzy match the interview type
                for t in available:
                    if t in type_lower:
                        interview_type = t
                        break

            self._speak(f"Great. We will do a {interview_type} interview.")

        self._speak("Let us begin. Good luck!")
        time.sleep(0.5)

        # ── Get questions for this interview type ──────────────────────────
        questions = self.question_bank.get_questions(interview_type, max_questions=5)
        total_score = 0
        questions_data = []  # For report generation

        # ── Question Loop ──────────────────────────────────────────────────
        for i, q_data in enumerate(questions, 1):
            question = q_data["q"] if isinstance(q_data, dict) else q_data
            topic = q_data.get("topic", "general") if isinstance(q_data, dict) else "general"

            # Transition phrase (not for first question)
            if i > 1:
                self._speak(random.choice(self._transition_phrases))
                time.sleep(0.3)

            # ✅ Attentive posture before asking
            self._look_center()
            self._speak(f"Question {i} of {len(questions)}: {question}")

            # ── Patient listener — 2 attempts, natural pause ──────────────
            encourage = random.choice(self._encourage_phrases)
            answer = self.stt.listen_patient(
                first_timeout=10,
                retry_timeout=15,
                phrase_time_limit=45,
                encourage_phrase=encourage,
                speak_fn=self._speak,
            )

            if not answer:
                answer = ""
                self._speak("I could not hear your answer. Let us move to the next question.")
            else:
                word_count = len(answer.split())

                # ── If answer is very short — ask to elaborate ────────────
                if word_count < 5:
                    elaborate = random.choice(self._elaborate_phrases)
                    self._speak(elaborate)

                    extra = self.stt.listen_patient(
                        first_timeout=8,
                        retry_timeout=0,
                        phrase_time_limit=30,
                        encourage_phrase=None,
                        speak_fn=None,
                    )
                    if extra:
                        answer = answer + " " + extra

                self._nod()  # ✅ Acknowledge the answer with a small nod
                self._speak("Okay, noted.")

            # ── AI-powered evaluation ─────────────────────────────────────
            eval_result = self.evaluator.evaluate(question, answer, topic)
            score = eval_result["score"]
            feedback = eval_result["feedback"]
            grade = eval_result["grade"]
            total_score += score

            # ── Clean feedback for TTS (max 2 sentences, no quotes) ───────
            feedback = feedback.strip('"').strip("'").strip()
            sentences = feedback.split(".")
            feedback = ". ".join(s.strip() for s in sentences[:2] if s.strip())
            if feedback and not feedback.endswith("."):
                feedback += "."

            # ── Verbal feedback (makes it feel like a real interview) ─────
            if score >= 7.0:
                self._speak(f"Good answer! {feedback}")
            elif score >= 4.0:
                self._speak(feedback)
            else:
                self._speak(f"Noted. {feedback}")

            # ── Save answer to database ───────────────────────────────────
            self.db.execute("""
                INSERT INTO interview_answers
                (interview_id, question, answer_text, score, confidence_score, emotion_state, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                interview_id,
                question,
                answer,
                score,
                eval_result.get("relevance", 0.0),
                grade,
                feedback,
            ))

            # Save for report
            questions_data.append({
                "question": question,
                "answer": answer,
                "score": score,
                "feedback": feedback,
                "grade": grade,
            })

        # ── Calculate final results ────────────────────────────────────────
        avg_score = total_score / len(questions) if questions else 0
        end_time = datetime.now().isoformat()
        summary = f"Interview completed. Average score: {avg_score:.1f}/10. Grade: {self._score_to_grade(avg_score)}"

        # ── Update interview record ────────────────────────────────────────
        self.db.execute("""
            UPDATE interviews
            SET end_time = ?, total_score = ?, status = ?, summary = ?
            WHERE id = ?
        """, (end_time, avg_score, "completed", summary, interview_id))

        # ── Generate professional report ───────────────────────────────────
        report_path = self.report_generator.generate(
            interview_id=interview_id,
            candidate_name=candidate_name,
            interview_type=interview_type,
            start_time=start_time,
            end_time=end_time,
            questions_data=questions_data,
            total_score=avg_score,
        )

        # ── Final verbal summary ───────────────────────────────────────────
        self._speak("Interview completed. Thank you for your time, " + candidate_name + ".")
        self._speak(f"Your average score is {avg_score:.1f} out of 10.")
        self._speak(f"Your overall grade is {self._score_to_grade(avg_score)}.")

        if avg_score >= 8.0:
            self._speak("Excellent performance! You did really well.")
        elif avg_score >= 6.0:
            self._speak("Good job! There is room for improvement but you did well overall.")
        elif avg_score >= 4.0:
            self._speak("You need to work on giving more detailed answers. Keep practicing!")
        else:
            self._speak("I recommend more preparation. Practice explaining concepts in detail.")

        self._speak("Your detailed report has been saved. All the best!")
        print(f"[INTERVIEW] Report saved: {report_path}")

        return interview_id, avg_score

    @staticmethod
    def _score_to_grade(score: float) -> str:
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