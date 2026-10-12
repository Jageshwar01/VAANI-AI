"""
VaaniAI — Chat Engine
Connects to Ollama (local LLM server) for AI-powered conversations.
Fully offline — no internet needed after model is downloaded.

Usage:
    engine = ChatEngine()
    response = engine.respond("What is Python?", person_name="Jageshwer")
    print(response)
"""

import requests
import json

from ai.conversation.prompt_builder import PromptBuilder
from ai.conversation.response_filter import ResponseFilter
from app.config import FAST_AI_MODEL, SMART_AI_MODEL, OLLAMA_URL


class ChatEngine:
    """
    AI conversation engine using Ollama local LLM.

    Features:
    - Maintains conversation history (last 10 exchanges)
    - Person-aware (uses face recognition name)
    - Mode-aware (social/interview/admin personality)
    - Memory-aware (recalls past interactions)
    - Response filtering for TTS
    """

    def __init__(self):
        self.fast_model = FAST_AI_MODEL
        self.smart_model = SMART_AI_MODEL
        self.url = OLLAMA_URL
        self.history: list[dict] = []    # [{"user": ..., "ai": ...}, ...]
        self._model_cache = {}           # {"model_name": True/False}

    def is_available(self, model_name: str) -> bool:
        """Check if Ollama server is running and a specific model is available."""
        if model_name in self._model_cache:
            return self._model_cache[model_name]

        try:
            r = requests.get(f"{self.url}/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                model_base = model_name.split(":")[0]
                is_ok = any(model_base in m for m in models)
                
                if not is_ok:
                    print(f"[AI] Model '{model_name}' not found. Available: {models}")
                    print(f"[AI] Run: ollama pull {model_name}")
                
                self._model_cache[model_name] = is_ok
                return is_ok
        except Exception as e:
            print(f"[AI] Ollama not reachable at {self.url}: {e}")
            print("[AI] Make sure Ollama is running: start Ollama app or run 'ollama serve'")

        self._model_cache[model_name] = False
        return False

    def respond(
        self,
        user_text: str,
        person_name: str = "guest",
        mode: str = "social",
        memories: list | None = None,
        language_mode: str = "en",
        knowledge_context: str = "",
    ) -> str:
        """
        Generate an AI response to the user's input.

        Args:
            user_text:    What the user said
            person_name:  Who is speaking (from face recognition)
            mode:         Current robot mode (social/interview/admin/idle)
            memories:     Recent memory entries for this person
            language_mode: "hi" or "en" to enforce hard language generation.
            knowledge_context: Relevant facts from the Knowledge Base.

        Returns:
            Cleaned, TTS-ready response string
        """
        # ── Determine which model to use based on mode ────────────────────
        # Fast model for social/idle/presentation (instant), Smart model for interview
        if mode in ["interview", "admin"]:
            active_model = self.smart_model
        else:
            active_model = self.fast_model

        # ── Check Ollama availability ─────────────────────────────────────
        if not self.is_available(active_model):
            # If smart model isn't downloaded, automatically fallback to fast model
            if active_model == self.smart_model and self.is_available(self.fast_model):
                print(f"[AI] Smart model {self.smart_model} not found, falling back to {self.fast_model}")
                active_model = self.fast_model
            else:
                return self._fallback_response(user_text)

        # ── Force constraint on small models ──────────────────────────────
        if language_mode == "hi":
            user_text += " (Reply in Hindi Devanagari only)"

        # ── Build prompt ──────────────────────────────────────────────────
        messages = PromptBuilder.build(
            user_text=user_text,
            person_name=person_name,
            mode=mode,
            history=self.history,
            memories=memories,
            language_mode=language_mode,
            knowledge_context=knowledge_context,
        )

        # ── Call Ollama ───────────────────────────────────────────────────
        try:
            print(f"[AI] Sending to Ollama ({active_model})...")

            response = requests.post(
                f"{self.url}/api/chat",
                json={
                    "model": active_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 300 if mode == "presentation" else 60,  # 300 tokens for presentation
                        "repeat_penalty": 1.1,
                    }
                },
                timeout=90   # 90s — first call pe model loading mein 60s+ lag sakta hai
            )

            if response.status_code == 200:
                data = response.json()
                raw_text = data.get("message", {}).get("content", "")

                # Filter for TTS
                clean_text = ResponseFilter.clean(raw_text)

                # Save to history
                self.history.append({
                    "user": user_text,
                    "ai": clean_text,
                })

                # Keep history manageable
                if len(self.history) > PromptBuilder.MAX_HISTORY:
                    self.history = self.history[-PromptBuilder.MAX_HISTORY:]

                return clean_text
            else:
                print(f"[AI] Ollama error {response.status_code}: {response.text[:200]}")
                return self._fallback_response(user_text)

        except requests.Timeout:
            print("[AI] Ollama timeout. Model may still be loading into RAM...")
            print("[AI] First call is slow (60-90s). Next calls will be fast (3-5s).")
            return "I need a moment to think. My brain is loading. Please ask me again."

        except requests.ConnectionError:
            print("[AI] Cannot connect to Ollama. Is it running?")
            self._ollama_ok = False   # reset cache
            return self._fallback_response(user_text)

        except Exception as e:
            print(f"[AI ERROR] {e}")
            return self._fallback_response(user_text)

    def clear_history(self):
        """Clear conversation history — call when changing modes or persons."""
        self.history.clear()

    def _fallback_response(self, user_text: str) -> str:
        """
        Simple fallback when Ollama is not available.
        Basic keyword responses so robot doesn't go completely silent.
        """
        text = user_text.lower()

        if any(w in text for w in ["hello", "hi", "hey", "namaste"]):
            return "Hello! I am VaaniAI. How can I help you?"

        if any(w in text for w in ["your name", "who are you", "naam"]):
            return "I am VaaniAI, a humanoid robot."

        if any(w in text for w in ["who made", "who built", "kisne banaya"]):
            return "Jageshwer built me."

        if any(w in text for w in ["how are you", "kaise ho", "kya haal"]):
            return "I am doing well, thank you for asking!"

        if any(w in text for w in ["thank", "shukriya", "dhanyavaad"]):
            return "You are welcome!"

        if any(w in text for w in ["time", "samay", "waqt"]):
            from datetime import datetime
            now = datetime.now().strftime("%I:%M %p")
            return f"The current time is {now}."

        return "I understand you, but my AI brain is not active right now. Please start Ollama."
