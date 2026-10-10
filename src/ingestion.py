import os
import asyncio
from datetime import datetime
from db_utils import get_db_pool, insert_filing
from edgar import Company, set_identity
from dotenv import load_dotenv

load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL")
MY_NAME = os.getenv("MY_NAME")

set_identity(f"{MY_NAME} {MY_EMAIL}")

form_type = ("10-K", "8-K", "10-Q")

async def get_data(pool, ticker: str):
    company = Company(f"{ticker}")

    current_year = datetime.now().year
    start_year = current_year - 5
    
    for form in form_type:
        filing_collection = company.get_filings(
            form=form, 
            filing_date=f"{start_year}-01-01:{current_year}-12-31"
        )
        for filing in filing_collection:
            fiscal_year = int(filing.filing_date.split('-')[0])
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


async def main():
    pool = await get_db_pool()

    try:
        await get_data(pool, 'AAPL')
    finally:
        await pool.close()

if __name__ == '__main__':
    asyncio.run(main())