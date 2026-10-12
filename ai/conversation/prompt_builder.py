"""
VaaniAI — Prompt Builder
Builds context-rich prompts for the LLM by combining:
  - System prompt (personality)
  - Person context (who is speaking, past memories)
  - Conversation history (last N messages)
  - Current user message
"""

from ai.conversation.personality import get_system_prompt


class PromptBuilder:
    """
    Constructs the full message list for ollama.chat().
    """

    MAX_HISTORY = 10   # Keep last 10 exchanges (20 messages) in context

    @staticmethod
    def build(
        user_text: str,
        person_name: str = "guest",
        mode: str = "social",
        history: list[dict] | None = None,
        memories: list | None = None,
        language_mode: str = "en",
        knowledge_context: str = "",
    ) -> list[dict]:
        """
        Build the messages list for the LLM.

        Args:
            user_text:   Current user input
            person_name: Name of person (from face recognition)
            mode:        Current robot mode
            history:     List of {"user": ..., "ai": ...} dicts
            memories:    Recent memory entries for this person
            language_mode: Hardware language toggle ("en" or "hi")
            knowledge_context: Relevant facts from Knowledge Base

        Returns:
            List of {"role": "system"|"user"|"assistant", "content": ...}
        """
        messages = []

        # ── System prompt ─────────────────────────────────────────────────
        system = get_system_prompt(mode, language_mode)

        # Add person context
        if person_name and person_name != "guest" and person_name != "Unknown":
            system += f"\nYou are currently talking to {person_name}. Use their name naturally in conversation."

        # Add memory context
        if memories:
            memory_text = "\nRecent interactions with this person:\n"
            for mem in memories[-5:]:   # last 5 memories
                # memory row: id, person_name, interaction_text, ai_response, tag, created_at
                try:
                    if isinstance(mem, (list, tuple)):
                        user_txt = mem[2]
                        ai_txt = mem[3] if len(mem) > 3 else None
                    else: # dict/sqlite3.Row
                        user_txt = mem.get('interaction_text', '')
                        ai_txt = mem.get('ai_response', None)
                        
                    memory_text += f"- User: {user_txt}\n"
                    if ai_txt:
                        memory_text += f"  VaaniAI: {ai_txt}\n"
                except Exception:
                    pass
            system += memory_text

        # ✅ Add Knowledge Base context (university, custom facts, etc.)
        # Force small models to ONLY use provided facts — they hallucinate otherwise
        if knowledge_context:
            system += "\n\nCRITICAL RULE: You have been given RELEVANT KNOWLEDGE below."
            system += "\nYou MUST answer ONLY using these facts. Do NOT invent or guess any information."
            system += "\nIf the answer is not in the knowledge, say 'I do not have that information.'"
            system += knowledge_context

        messages.append({"role": "system", "content": system})

        # ── Conversation history ──────────────────────────────────────────
        if history:
            for exchange in history[-PromptBuilder.MAX_HISTORY:]:
                messages.append({"role": "user", "content": exchange["user"]})
                messages.append({"role": "assistant", "content": exchange["ai"]})

        # ── Current user message ──────────────────────────────────────────
        messages.append({"role": "user", "content": user_text})

        return messages
