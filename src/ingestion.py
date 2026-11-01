import os
import asyncio
from typing import cast
from datetime import datetime, date
from db_utils import get_db_pool, insert_filing
from edgar import Company, set_identity
from dotenv import load_dotenv

load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL")
MY_NAME = os.getenv("MY_NAME")

set_identity(f"{MY_NAME} {MY_EMAIL}")

form_type = ("10-K", "8-K", "10-Q")

async def sync_parse_and_chunk(filing_obj, form):
    html_content = filing_obj.html()
    


async def ingest_filing_data(pool, ticker: str):
    company = Company(f"{ticker}")

    current_year = datetime.now().year
    start_year = current_year - 5
    
    for form in form_type:
        filing_collection = company.get_filings(
            form=form, 
            filing_date=f"{start_year}-01-01:{current_year}-12-31"
        )
        for filing in filing_collection:
            filing_date = cast(date, filing.filing_date)
            fiscal_year = filing_date.year
            assert filing.document is not None
            filing_data = {
                'cik': filing.cik,
                'company_name': filing.company,
                'ticker': ticker,
                'form_type': form,
                'filing_date': filing.filing_date,
                'fiscal_year': fiscal_year,
                'accession_no': filing.accession_no,
                'source_url': filing.document.url
            }
            filing_ID = await insert_filing(pool=pool, filing_data=filing_data)
            assert filing_ID is not None
            await ingest_section_data(filing_id=filing_ID, form=form, filing_obj=filing)

async def ingest_section_data(filing_id: str, form:str, filing_obj):
    parsed_sections = await asyncio.to_thread(sync_parse_and_chunk, filing_obj=filing_obj, form=form)





async def main():
    pool = await get_db_pool()

    try:
        await ingest_filing_data(pool, 'AAPL')
    finally:
        await pool.close()

if __name__ == '__main__':
    asyncio.run(main())