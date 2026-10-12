"""
VaaniAI — Knowledge Base (RAG)
Loads custom .txt files from data/knowledge/ and retrieves relevant facts
to inject into the AI prompt. No retraining needed — just edit text files!
"""

import os
import re


class KnowledgeBase:
    """
    Simple keyword-based knowledge retrieval system.
    Reads all .txt files from data/knowledge/ and finds relevant facts
    based on the user's question.
    """

    def __init__(self, knowledge_dir: str = "data/knowledge"):
        self.knowledge_dir = knowledge_dir
        self.facts: list[dict] = []  # {"text": "...", "source": "filename.txt"}
        self.load_all()

    def load_all(self):
        """Load all .txt files from the knowledge directory."""
        self.facts = []

        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir, exist_ok=True)
            print(f"[KNOWLEDGE] Created empty knowledge directory: {self.knowledge_dir}")
            return

        file_count = 0
        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.knowledge_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            # Skip empty lines and comments
                            if line and not line.startswith("#"):
                                self.facts.append({
                                    "text": line,
                                    "source": filename,
                                })
                    file_count += 1
                except Exception as e:
                    print(f"[KNOWLEDGE] Error reading {filename}: {e}")

        print(f"[KNOWLEDGE] Loaded {len(self.facts)} facts from {file_count} files.")

    def reload(self):
        """Hot-reload all knowledge files without restarting the robot."""
        self.load_all()

    def search(self, query: str, max_results: int = 5) -> list[str]:
        """
        Find facts relevant to the user's query using keyword matching.
        Returns a list of fact strings sorted by relevance.
        """
        if not self.facts:
            return []

        query_lower = query.lower()
        # Extract meaningful words (3+ chars, skip common words)
        stop_words = {
            "the", "is", "are", "was", "were", "what", "who", "how", "where",
            "when", "why", "can", "you", "your", "tell", "about", "please",
            "me", "do", "does", "did", "have", "has", "this", "that",
            "kya", "hai", "kaise", "kahan", "kaun", "batao", "bolo",
            "mujhe", "mera", "tera", "aap", "tum", "hum",
        }
        query_words = [
            w for w in re.findall(r'\w+', query_lower)
            if len(w) >= 3 and w not in stop_words
        ]

        if not query_words:
            return []

        # Score each fact by how many query words it contains
        scored = []
        for fact in self.facts:
            fact_lower = fact["text"].lower()
            score = sum(1 for word in query_words if word in fact_lower)
            if score > 0:
                scored.append((score, fact["text"]))

        # Sort by score (highest first) and return top results
        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:max_results]]

    def get_context_string(self, query: str) -> str:
        """
        Get a formatted context string to inject into the AI prompt.
        Returns empty string if no relevant facts found.
        """
        results = self.search(query)
        if not results:
            return ""

        context = "\n\nRELEVANT KNOWLEDGE (use these facts to answer):\n"
        for fact in results:
            context += f"- {fact}\n"
        return context
