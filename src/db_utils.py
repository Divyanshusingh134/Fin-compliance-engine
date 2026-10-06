import os
from dotenv import load_dotenv
import asyncpg
from pgvector.asyncpg import register_vector

load_dotenv()


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


async def insert_filing(pool, filing_data: dict) -> str | None:
    INSERT_FILING_QUERY = """INSERT INTO filings(
    cik, company_name, ticker, form_type, filing_date, fiscal_year, accession_no, source_url) 
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (accession_no) DO NOTHING RETURNING filing_id"""

    async with pool.acquire() as conn:
        return await conn.fetchval(
            INSERT_FILING_QUERY,
            filing_data["cik"],
            filing_data["company_name"],
            filing_data["ticker"],
            filing_data["form_type"],
            filing_data["filing_date"],
            filing_data["fiscal_year"],
            filing_data["accesssion_no"],
            filing_data["source_url"]
        )
    

async def insert_section(pool, section_data: dict) -> str | None:
    ...

async def chunks_filing(pool, chunks_data: dict) -> str | None:
    ...