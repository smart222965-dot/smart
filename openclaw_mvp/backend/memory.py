import psycopg2
from psycopg2 import sql
import redis
import yaml
import os

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

config = load_config()

class MemoryManager:
    def __init__(self):
        self.db_config = config.get('db', {})
        self.redis_config = config.get('redis', {})
        # PostgreSQL
        try:
            self.conn = psycopg2.connect(
                dbname=self.db_config.get('name', 'openclaw_mvp_db'),
                user=self.db_config.get('user', 'openclaw_user'),
                password=self.db_config.get('password', 'your_secure_db_password'),
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432)
            )
            self.cursor = self.conn.cursor()
            self.ensure_tables()
        except Exception as e:
            print(f"DB connection error: {e}")
            self.conn = None
            self.cursor = None

        # Redis
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            print(f"Redis connection error: {e}")
            self.redis_client = None

    def ensure_tables(self):
        if not self.cursor:
            return
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_text TEXT,
                    ai_response TEXT,
                    action_performed TEXT,
                    action_result TEXT,
                    timestamp TIMESTAMPTZ DEFAULT now()
                );
            """)
            self.conn.commit()
        except Exception as e:
            print(f"Memory table setup error: {e}")
            self.conn.rollback()

    def log_conversation_turn(self, user_text: str, ai_response: str | None, action_performed: str | None = None, action_result: str | None = None):
        if not self.cursor:
            return
        try:
            self.cursor.execute("""
                INSERT INTO conversations (user_text, ai_response, action_performed, action_result)
                VALUES (%s, %s, %s, %s);
            """, (user_text, ai_response, action_performed, action_result))
            self.conn.commit()
        except Exception as e:
            print(f"Memory log error: {e}")
            self.conn.rollback()

    def get_recent_logs(self, limit: int = 10) -> list:
        if not self.cursor:
            return []
        try:
            self.cursor.execute("""
                SELECT id, user_text, ai_response, action_performed, action_result, timestamp
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT %s;
            """, (limit,))
            rows = self.cursor.fetchall()
            logs = []
            for r in rows:
                logs.append({
                    "id": r[0],
                    "user_text": r[1],
                    "ai_response": r[2],
                    "action_performed": r[3],
                    "action_result": r[4],
                    "timestamp": r[5].isoformat()
                })
            return logs
        except Exception as e:
            print(f"Memory fetch error: {e}")
            return []

    def cache_response(self, key: str, value: str, ttl: int = 300):
        if not self.redis_client:
            return
        try:
            self.redis_client.setex(key, ttl, value)
        except Exception as e:
            print(f"Redis cache error: {e}")

    def get_cached_response(self, key: str):
        if not self.redis_client:
            return None
        try:
            return self.redis_client.get(key)
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

memory_manager = MemoryManager()
