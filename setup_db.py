import asyncio
from pathlib import Path
from src.db_utils import get_db_pool

SCHEMA_PATH = Path(__file__).parent / "sql" / "01_schema.sql"


async def init_db():
    pool = await get_db_pool()
    
    sql_schema = SCHEMA_PATH.read_text(encoding="utf-8")
                                       
    async with pool.acquire() as conn:
        print("Executing schema migration...")
        await conn.execute(sql_schema)
        print("Schema successfully applied.")

    await pool.close()

if __name__ == "__main__":
    asyncio.run(init_db())




