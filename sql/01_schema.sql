CREATE EXTENSION IF NOT EXISTS vector;


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
    CONSTRAINT uq_sections UNIQUE(filing_id, item_no)
);

CREATE TABLE IF NOT EXISTS chunks(
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    filing_id UUID NOT NULL REFERENCES filings(filing_id) ON DELETE CASCADE,
    section_id UUID NOT NULL REFERENCES sections(section_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL, 
    raw_text TEXT NOT NULL,
    lexical_search tsvector GENERATED ALWAYS AS (to_tsvector('english', raw_text)) STORED, 
    embedding vector(768),
    CONSTRAINT uq_filing_chunks UNIQUE(section_id, chunk_index)
);

CREATE INDEX full_text_search ON chunks USING GIN(lexical_search);
CREATE INDEX chunk_filing ON chunks(filing_id, chunk_index);
CREATE INDEX cosine_similarity_search ON chunks USING hnsw(embedding vector_cosine_ops) WITH (m = 16, ef_construction= 64);

CREATE TABLE IF NOT EXISTS agreements(
    agreement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filing_id UUID NOT NULL REFERENCES filings(filing_id) ON DELETE CASCADE,
    agreement_name TEXT, 
    agreement_type TEXT NOT NULL, 
    effective_date DATE , 
    exhibit_reference TEXT NOT NULL, 
    CONSTRAINT uq_agreements UNIQUE(filing_id, exhibit_reference)
);

CREATE TABLE IF NOT EXISTS agreement_chunks(
    agreement_chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    agreement_id UUID NOT NULL REFERENCES agreements(agreement_id) ON DELETE CASCADE, 
    filing_id UUID NOT NULL REFERENCES filings(filing_id) ON DELETE CASCADE, 
    chunk_index INTEGER NOT NULL, 
    raw_text TEXT NOT NULL, 
    lexical_search tsvector GENERATED ALWAYS AS (to_tsvector('english', raw_text)) STORED, 
    embedding vector(768),
    CONSTRAINT uq_agreements_chunks UNIQUE(agreement_id, chunk_index)
);

CREATE INDEX full_text_search_agreements ON agreement_chunks USING GIN(lexical_search);
CREATE INDEX chunk_filin_agreements ON agreement_chunks(filing_id, chunk_index);
CREATE INDEX cosine_similarity_search_agreements ON agreement_chunks USING hnsw(embedding vector_cosine_ops) WITH (m = 16, ef_construction= 64);