import os
import logging
import sqlite3
from pathlib import Path
from datasketch import MinHash
from minhash_utils import serialize_minhash, deserialize_minhash

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        try:
            self.create_table()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS order_history
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, minhash TEXT)''')
        conn.close()

    def get_all_entries(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for row in cursor.execute("SELECT id, user_id, minhash FROM order_history"):
            id, user_id, minhash_json = row
            minhash = deserialize_minhash(minhash_json)
            yield id, user_id, minhash
        conn.close()

    def save_minhash(self, user_id: str, minhash: MinHash):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        minhash_json = serialize_minhash(minhash)
        cursor.execute("INSERT INTO order_history (user_id, minhash) VALUES (?, ?)",
                       (user_id, minhash_json))
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id

    def get_by_id(self, entry_id: int):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, minhash FROM order_history WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                id, user_id, minhash_json = row
                minhash = deserialize_minhash(minhash_json)
                return id, user_id, minhash
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error in get_by_id: {e}")
            raise
