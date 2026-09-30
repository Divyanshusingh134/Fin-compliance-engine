import os
import asyncpg
from pgvector.asyncpg import register_vector

async def setup_connection(conn):
    await register_vector(conn)

async def get_db_pool():
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DB"),
        min_size=2,
        max_size=10,
        init=setup_connection
    )
    return pool