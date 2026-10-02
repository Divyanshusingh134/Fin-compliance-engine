CREATE TABLE IF NOT EXISTS filings(
    filing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cik VARCHAR(10) NOT NULL,
    company_name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    form_type TEXT NOT NULL, 
    filing_date DATE NOT NULL, 
    fiscal_year INTEGER NOT NULL, 
    accession_no TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL
);

CREATE INDEX filings_indx ON filings(ticker, fiscal_year, form_type);

CREATE TABLE IF NOT EXISTS sections(
    section_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    filing_id UUID NOT NULL REFERENCES filings(filing_id) ON DELETE CASCADE,
    item_no TEXT NOT NULL,
    item_title TEXT NOT NULL,
    word_count INTEGER,
    CONSTRAINT uq_filing_section UNIQUE (filing_id, item_no)

);

CREATE TABLE IF NOT EXISTS chunks(
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    filing_id UUID NOT NULL REFERENCES filings(filing_id),
    section_id UUID NOT NULL REFERENCES sections(section_id),
    chunk_index INTEGER NOT NULL, 
    raw_text TEXT NOT NULL,
    lexical_search tsvector, 
    semantic_search vector(786),
    CONSTRAINT uq_filing_chunks UNIQUE(filing_id,section_id chunk_index)
);

CREATE INDEX full_text_search ON lexical_search USING GIN(to_tsvector('english', raw_text))
CREATE INDEX vector_search ON semantic_search USING hnsw(raw_text)

