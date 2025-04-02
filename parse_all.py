#!/usr/bin/env python
import os
import json
import glob
import logging
from custom_parser import InvestorProfileParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parse_all.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Parse all HTML files in the output/html directory."""
    # Find all HTML files
    html_files = glob.glob("output/html/*.html")
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    # Process each HTML file
    results = []
    for html_file in html_files:
        logger.info(f"Processing {html_file}")
        try:
            # Read HTML content
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Parse investor profile
            parser = InvestorProfileParser(html_content, html_file)
            investor_data = parser.parse()
            
            # Add to results
            results.append(investor_data)
            logger.info(f"Added data for {html_file}")
        except Exception as e:
            logger.error(f"Failed to process {html_file}: {str(e)}")
    
    # Save results to JSON file
    output_file = "output/investor_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Successfully saved data for {len(results)} investors to {output_file}")
    
    # Print statistics about new fields
    roles_count = sum(1 for inv in results if inv.get("roles"))
    areas_count = sum(1 for inv in results if inv.get("areas_of_interest"))
    coinvestors_count = sum(1 for inv in results if inv.get("co_investors"))
    scouts_count = sum(1 for inv in results if inv.get("scouts_angels"))
    fund_size_count = sum(1 for inv in results if inv.get("current_fund_size"))
    
    logger.info("New field statistics:")
    logger.info(f" - Investors with roles: {roles_count}")
    logger.info(f" - Investors with areas of interest: {areas_count}")
    logger.info(f" - Investors with co-investors: {coinvestors_count}")
    logger.info(f" - Investors with scouts & angels: {scouts_count}")
    logger.info(f" - Investors with fund size: {fund_size_count}")

if __name__ == "__main__":
    main() 