from datetime import datetime

class MemoryManager:
    def __init__(self, db):
        self.db = db

    def add_memory(self, person_name, interaction_text, ai_response=None, tag="general"):
        self.db.execute("""
            INSERT INTO memory_logs (person_name, interaction_text, ai_response, tag, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (person_name, interaction_text, ai_response, tag, datetime.now().isoformat()))

    def get_recent_memories(self, person_name):
        cursor = self.db.execute("""
            SELECT * FROM memory_logs
            WHERE person_name = ?
            ORDER BY id DESC
            LIMIT 5
        """, (person_name,))
        return cursor.fetchall()