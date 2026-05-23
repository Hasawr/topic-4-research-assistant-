# src/storage/db_store.py
import asyncpg
from src.config import settings

class PostgresStore:
    def __init__(self):
        self.db_url = settings.DATABASE_URL

    async def init_db(self):
        """my_table cədvəlinin yaradılması"""
        conn = await asyncpg.connect(self.db_url)
        try:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS my_table (
                    id SERIAL PRIMARY KEY,
                    topic TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        finally:
            await conn.close()

    async def save_research_result(self, topic: str, result: str):
        """Nəticələrin my_table cədvəlinə yazılması"""
        conn = await asyncpg.connect(self.db_url)
        try:
            # SQL inyeksiyalarının qarşısını almaq üçün parametrli sorğu
            await conn.execute(
                'INSERT INTO my_table (topic, result) VALUES ($1, $2)',
                topic, result
            )
            print(f"Məlumat my_table cədvəlinə uğurla yazıldı: {topic}")
        finally:
            await conn.close()

    async def get_research_result(self, topic: str):
        """Məlumatın my_table cədvəlindən oxunması"""
        conn = await asyncpg.connect(self.db_url)
        try:
            row = await conn.fetchrow(
                'SELECT result FROM my_table WHERE topic = $1 ORDER BY created_at DESC LIMIT 1',
                topic
            )
            return row['result'] if row else None
        finally:
            await conn.close()