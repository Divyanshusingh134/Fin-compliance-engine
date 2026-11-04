import os
import json
import asyncio
import logging
from typing import cast
from datetime import datetime, date
from edgar import Company, set_identity
from dotenv import load_dotenv

from db_utils import get_db_pool, insert_filing, insert_section, insert_chunks
from parser import parse_filing
from chunker import Chunker
from llm import embed
load_dotenv()

logger = logging.getLogger(__name__)

MY_EMAIL = os.getenv("MY_EMAIL")
MY_NAME = os.getenv("MY_NAME")

set_identity(f"{MY_NAME} {MY_EMAIL}")

form_type = ("10-K", "8-K", "10-Q")

SEC_ITEM_TITLE = {
    "ITEM 1": "Business",
    "ITEM 1A": "Risk Factors",
    "ITEM 1B": "Unresolved Staff Comments",
    "ITEM 1C": "Cybersecurity",
    "ITEM 2": "Properties",
    "ITEM 3": "Legal Proceedings",
    "ITEM 5": "Market for Registrant's Common Equity",
    "ITEM 7": "Management's Discussion and Analysis",
    "ITEM 7A": "Quantitative and Qualitative Disclosures About Market Risk",
    "ITEM 8": "Financial Statements and Supplementary Data",
    "ITEM 9": "Changes in and Disagreements with Accountants",
    "ITEM 9A": "Controls and Procedures"
}

def sync_parse_and_chunk(filing_obj, form) ->dict:
    html_content = filing_obj.html()
    raw_sections = parse_filing(html=html_content)

    processed_data = {}
    for sec_item, blocks in raw_sections.items():
        part_no = sec_item[0] if sec_item else "UNKNOWN"
        item_no = sec_item[1] if sec_item and len(sec_item) > 1 else "UNKNOWN"

        item_title = SEC_ITEM_TITLE.get(f'ITEM {item_no}')

        chunker = Chunker(blocks=blocks)
        chunks = chunker.walk()

        processed_data[item_no] = {
            "part_no": part_no,
            "title": item_title,
            "word_count": sum(len(c['text'].split()) for c in chunks),
            "chunks": chunks
        }
    return processed_data


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
            # filing_date = cast(date, filing.filing_date)
            # fiscal_year = filing_date.year
            fiscal_year = int(str(filing.filing_date).split('-')[0])
            actual_date_obj = datetime.strptime(str(filing.filing_date), "%Y-%m-%d").date()
            assert filing.document is not None
            filing_data = {
                'cik': filing.cik,
                'company_name': filing.company,
                'ticker': ticker,
                'form_type': form,
                'filing_date': actual_date_obj,
                'fiscal_year': fiscal_year,
                'accession_no': filing.accession_no,
                'source_url': filing.document.url
            }
            filing_ID = await insert_filing(pool=pool, filing_data=filing_data)
            if filing_ID is None:
                logging.info(f"Filing {filing.accession_no} already exists. Skipping.")
                continue
            await ingest_section_data(pool=pool, filing_id=filing_ID, form=form, filing_obj=filing)

async def ingest_section_data(pool, filing_id: str, form:str, filing_obj):
    parsed_sections = await asyncio.to_thread(sync_parse_and_chunk, filing_obj=filing_obj, form=form)

    for item_no, data in parsed_sections.items():
        section_data = {
            "filing_id": filing_id,
            "part_no": data.get("part_no"),
            "item_no": f"ITEM {item_no}",
            "item_title": data.get("title"),
            "word_count": data.get("word_count")
        }
        section_ID = await insert_section(pool=pool, section_data=section_data)

        if section_ID is None:
            continue

        await ingest_chunks_data(pool=pool, filing_id=filing_id, section_ID=section_ID, item_no=item_no, data=data)
        
        # raw_chunks = [c for c in data.get("chunks", []) if c.get("text", "").strip()]
        # if not raw_chunks:
        #     continue

        # text_to_embed = [c['text'] for c in raw_chunks]

        # embeddings = await embed(text_to_embed)
        # if embeddings is None:
        #     logger.error(f"Failed to embed chunks for {section_data['item_no']}")
        #     continue
        # chunks_batch = []
        # for idx, (chunk_dict, emb) in enumerate(zip(raw_chunks, embeddings)):
        #     heading_path = chunk_dict.get("heading_path")

        #     structured_data_dict = chunk_dict.get("rows", {})
        #     structured_data_json = json.dumps(structured_data_dict)

        #     chunks_batch.append((
        #         filing_id,
        #         section_ID,
        #         heading_path,
        #         idx,
        #         chunk_dict.get("text"),
        #         emb,
        #         structured_data_json
        #     ))
            
        # await insert_chunks(pool=pool, chunks_data=chunks_batch)

async def ingest_chunks_data(pool, filing_id, section_ID, item_no, data):
    raw_chunks = [c for c in data.get("chunks", []) if c.get('text', "").strip()]
    if not raw_chunks:
        return
    text_to_embed = [c["text"] for c in raw_chunks]

    embeddings = await embed(text_to_embed)
    if embeddings is None:
        logger.error(f"Failed to embed chunks for {item_no}")
        return
    chunks_batch = []
    for idx, (chunk_dict, emb) in enumerate(zip(raw_chunks, embeddings)):
        heading_path = chunk_dict.get("heading_path")

        structured_data_dict = chunk_dict.get("rows", {})
        structured_data_json = json.dumps(structured_data_dict)

        chunks_batch.append((
            filing_id,
            section_ID,
            heading_path,
            idx,
            chunk_dict.get("text"),
            emb,
            structured_data_json
        ))
        
    await insert_chunks(pool=pool, chunks_data=chunks_batch)



async def main():
    pool = await get_db_pool()

    try:
        await ingest_filing_data(pool, 'AAPL')
    finally:
        await pool.close()

if __name__ == '__main__':
    asyncio.run(main())