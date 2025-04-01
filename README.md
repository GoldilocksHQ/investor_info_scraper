# Apollo.io Investor Profile Scraper

A Python-based scraper for extracting investor data from Apollo.io profiles. The scraper uses a two-step approach:
1. First attempts to scrape with simple requests
2. Uses Playwright only when needed to expand investment tables

## Project Structure

```
.
├── scraper.py           # Main scraping script (requests + Playwright)
├── custom_parser.py     # Core parsing logic
├── parse_pages.py       # Orchestrates parsing of HTML files
├── summarize_data.py    # Analyzes extracted data
├── requirements.txt     # Python dependencies
└── output/
    ├── html/           # Downloaded HTML files
    ├── investor_data.json    # Extracted investor data
    └── investor_summary.json # Analysis results
```

## How to Use

1. **Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install Playwright browsers
   playwright install
   ```

2. **Scrape Investor Profiles**
   ```bash
   # Run the scraper
   python scraper.py
   ```
   This will:
   - Load URLs from `output/investor_urls.txt`
   - Download HTML files to `output/html/`
   - Save results to `output/download_results.json`

3. **Parse Investor Data**
   ```bash
   # Parse downloaded HTML files
   python parse_pages.py
   ```
   This will:
   - Read HTML files from `output/html/`
   - Extract investor data
   - Save to `output/investor_data.json`

4. **Generate Summary**
   ```bash
   # Analyze the extracted data
   python summarize_data.py
   ```
   This will:
   - Read data from `output/investor_data.json`
   - Generate statistics and insights
   - Save to `output/investor_summary.json`

## Data Extraction Methods

The scraper uses multiple methods to extract data:

1. **Primary Method**: Apollo State Extraction
   - Extracts data from the JavaScript Apollo state
   - Fastest and most reliable method
   - Contains complete investor information

2. **Fallback Method**: HTML Extraction
   - Used when Apollo state is not available
   - Parses the HTML structure directly
   - May miss some dynamic content

## Output Data Structure

The extracted data is saved in JSON format with the following structure:

```json
{
  "name": "Investor Name",
  "position": "Position",
  "firm": "Firm Name",
  "location": "Location",
  "investments": [
    {
      "company": "Company Name",
      "round": "Funding Round",
      "date": "Investment Date",
      "amount": "Investment Amount",
      "is_lead": true/false
    }
  ],
  "extraction_method": "apollo_state/html",
  "source_file": "filename.html"
}
```

## Requirements

- Python 3.8+
- BeautifulSoup4
- Requests
- Playwright
- LXML## Notes

- The scraper uses proxies to avoid rate limiting
- Random delays are added between requests
- Failed downloads are logged in `output/download_results.json`- HTML files are saved for debugging and reprocessing 


