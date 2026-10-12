import sqlite3
from app.config import DATABASE_PATH

class DatabaseManager:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT,
            relation_type TEXT,
            face_id TEXT,
            notes TEXT,
            last_seen TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT NOT NULL,
            interview_type TEXT,
            start_time TEXT,
            end_time TEXT,
            total_score REAL DEFAULT 0,
            status TEXT,
            summary TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER,
            question TEXT NOT NULL,
            answer_text TEXT,
            score REAL DEFAULT 0,
            confidence_score REAL DEFAULT 0,
            emotion_state TEXT,
            remarks TEXT,
            FOREIGN KEY(interview_id) REFERENCES interviews(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_name TEXT,
            interaction_text TEXT,
            ai_response TEXT,
            tag TEXT,
            created_at TEXT
        )
        """)

        # ✅ Auto-migration for self-learning (upgrade old table)
        try:
            cursor.execute("ALTER TABLE memory_logs ADD COLUMN ai_response TEXT")
        except sqlite3.OperationalError:
            # Column already exists
            pass

        self.conn.commit()

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def close(self):
        if self.conn:
            self.conn.close()