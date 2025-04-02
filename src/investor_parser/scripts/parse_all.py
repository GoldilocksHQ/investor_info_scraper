#!/usr/bin/env python

import os
import json
import glob
import logging
import shutil
from pathlib import Path

# Get the appropriate parser
try:
    # Try to import from src structure (if installed as package)
    from src.investor_parser.core.parser import InvestorProfileParser
except ImportError:
    # Fallback to local import
    import sys
    sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
    from custom_parser import InvestorProfileParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/parse_all.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
os.makedirs("data/output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def migrate_legacy_files():
    """Migrate files from legacy output/ directory to data/ directory."""
    # Migrate HTML files
    if os.path.exists("output/html"):
        logger.info("Checking for HTML files in legacy output/html directory")
        html_files = glob.glob("output/html/*.html")
        if html_files:
            logger.info(f"Found {len(html_files)} HTML files to migrate from output/html to data/html")
            os.makedirs("data/html", exist_ok=True)
            
            for html_file in html_files:
                filename = os.path.basename(html_file)
                dest_path = os.path.join("data/html", filename)
                
                # Only copy if the file doesn't exist in the data/html directory
                if not os.path.exists(dest_path):
                    logger.info(f"Migrating {html_file} -> {dest_path}")
                    shutil.copy2(html_file, dest_path)
    
    # Migrate investor data files
    if os.path.exists("output/investor_data.json") and not os.path.exists("data/output/investor_data.json"):
        logger.info("Migrating investor_data.json from output/ to data/output/")
        shutil.copy2("output/investor_data.json", "data/output/investor_data.json")
    
    # Migrate URL file
    if os.path.exists("output/investor_urls.txt") and not os.path.exists("data/investor_urls.txt"):
        logger.info("Migrating investor_urls.txt from output/ to data/")
        os.makedirs("data", exist_ok=True)
        shutil.copy2("output/investor_urls.txt", "data/investor_urls.txt")

def main():
    """Parse all HTML files in the data/html directory."""
    # Check for and migrate legacy files if needed
    migrate_legacy_files()
    
    # Find all HTML files
    html_files = glob.glob("data/html/*.html")
    if not html_files:
        # Try the old path as fallback
        old_path_files = glob.glob("output/html/*.html")
        if old_path_files:
            html_files = old_path_files
            logger.info(f"Using HTML files from legacy path: output/html/")
    
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
            logger.info(f"Successfully parsed {html_file}")
        except Exception as e:
            logger.error(f"Failed to process {html_file}: {str(e)}")
    
    if not results:
        logger.error("No investor profiles were successfully parsed.")
        return
    
    # Save results to JSON file
    output_file = "data/output/investor_data.json"
    
    # Make sure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
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