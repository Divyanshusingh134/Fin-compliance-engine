CREATE TABLE IF NOT EXISTS filings(
    filing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cik VARCHAR(10) NOT NULL,
    company_name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    form_type TEXT NOT NULL, 
    filing_date DATE NOT NULL, 
    fiscal_year INT NOT NULL, 
    accession_no TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL
);


