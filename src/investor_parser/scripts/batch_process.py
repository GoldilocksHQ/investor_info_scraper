#!/usr/bin/env python
"""
Process all investor profile HTML files in a batch.

This script reads all HTML files from the data/html directory,
extracts investor data, and saves the results to data/output/investor_data.json.
"""
import os
import glob
import json
import logging
from investor_parser.core.parser import InvestorProfileParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/batch_process.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    # Create output directory if it doesn't exist
    os.makedirs('data/output', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Get all HTML files in the html directory
    html_files = glob.glob('data/html/*.html')
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    # Process each HTML file
    investors_data = []
    for html_file in html_files:
        logger.info(f"Processing {html_file}")
        
        try:
            # Read the HTML file
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse the investor profile
            parser = InvestorProfileParser(html_content, html_file)
            data = parser.parse()
            
            # Add the data to the list
            investors_data.append(data)
            logger.info(f"Added data for {html_file}")
        except Exception as e:
            logger.error(f"Error processing {html_file}: {e}")
    
    # Save the data to a JSON file
    with open('data/output/investor_data.json', 'w', encoding='utf-8') as f:
        json.dump(investors_data, f, indent=2)
    
    logger.info(f"Successfully saved data for {len(investors_data)} investors to data/output/investor_data.json")
    
    # Log statistics about the extracted data
    roles_count = sum(1 for investor in investors_data if investor.get('roles'))
    aoi_count = sum(1 for investor in investors_data if investor.get('areas_of_interest'))
    coinvestors_count = sum(1 for investor in investors_data if investor.get('co_investors'))
    scouts_count = sum(1 for investor in investors_data if investor.get('scouts_angels'))
    fund_size_count = sum(1 for investor in investors_data if investor.get('current_fund_size'))
    
    logger.info("New field statistics:")
    logger.info(f" - Investors with roles: {roles_count}")
    logger.info(f" - Investors with areas of interest: {aoi_count}")
    logger.info(f" - Investors with co-investors: {coinvestors_count}")
    logger.info(f" - Investors with scouts & angels: {scouts_count}")
    logger.info(f" - Investors with fund size: {fund_size_count}")

if __name__ == "__main__":
    main() 