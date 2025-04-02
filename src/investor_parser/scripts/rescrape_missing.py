#!/usr/bin/env python
"""
Check for missing HTML files based on URLs in investor_urls.txt and rescrape them.

This script is used to:
1. Compare URLs in the investor_urls.txt file with existing HTML files
2. Identify any URLs that don't have corresponding HTML files
3. Rescrape those missing URLs

Usage:
    python -m src.investor_parser.scripts.rescrape_missing [--no-proxy] [--limit N]

Options:
    --no-proxy   Disable proxy usage
    --limit N    Limit the number of URLs to rescrape

This is useful when HTML files have been deleted or corrupted and need to be
regenerated without running the full scraper.
"""

import os
import re
import glob
import logging
import argparse
import subprocess
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/rescrape.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs("data/html", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def check_missing_html_files(url_file: str) -> list:
    """
    Check for missing HTML files based on URLs in the url_file.
    
    Args:
        url_file: Path to file with URLs to check
        
    Returns:
        List of URLs that need to be rescrapped
    """
    if not os.path.exists(url_file):
        logger.error(f"URL file not found: {url_file}")
        return []
    
    # Get all existing HTML files
    existing_files = set()
    for html_file in glob.glob("data/html/*.html"):
        existing_files.add(os.path.basename(html_file))
    
    # Also check legacy path if it exists
    if os.path.exists("output/html"):
        for html_file in glob.glob("output/html/*.html"):
            existing_files.add(os.path.basename(html_file))
    
    # Find missing files
    missing_urls = []
    
    try:
        with open(url_file, "r", encoding="utf-8") as f:
            for line in f:
                url = line.strip()
                if not url or url.startswith("#"):
                    continue
                
                # Extract the investor name from the URL
                match = re.search(r"/investors/([^/]+)", url)
                if match:
                    investor_name = match.group(1)
                    html_filename = f"investors-{investor_name}.html"
                    
                    if html_filename not in existing_files:
                        missing_urls.append(url)
    except Exception as e:
        logger.error(f"Error checking missing files: {str(e)}")
    
    logger.info(f"Found {len(missing_urls)} missing HTML files that need to be rescrapped")
    return missing_urls

def rescrape_missing_files(missing_urls: list, use_proxy: bool = True, limit: int = None) -> bool:
    """
    Rescrape missing HTML files.
    
    Args:
        missing_urls: List of URLs to rescrape
        use_proxy: Whether to use proxies
        limit: Maximum number of URLs to rescrape
        
    Returns:
        True if rescraping was successful, False otherwise
    """
    if not missing_urls:
        logger.info("No missing HTML files to rescrape")
        return True
    
    # Limit the number of URLs if requested
    if limit and limit < len(missing_urls):
        logger.info(f"Limiting rescrape to {limit} URLs (out of {len(missing_urls)} missing)")
        missing_urls = missing_urls[:limit]
    
    logger.info(f"Rescraping {len(missing_urls)} missing HTML files")
    
    # Create a temporary file with the missing URLs
    temp_url_file = "data/missing_urls.txt"
    with open(temp_url_file, "w", encoding="utf-8") as f:
        for url in missing_urls:
            f.write(f"{url}\n")
    
    # Run the scraper with the temporary file
    cmd = [sys.executable, "-m", "src.investor_parser.scripts.scrape_profiles", "--url-file", temp_url_file]
    
    if not use_proxy:
        cmd.append("--no-proxy")
        
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logger.info("Rescraping completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Rescraping failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logger.exception(f"Error running rescraper: {str(e)}")
        return False
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_url_file):
            os.unlink(temp_url_file)

def main():
    """
    Main function to check for missing HTML files and rescrape them.
    """
    parser = argparse.ArgumentParser(
        description="Check for missing HTML files and rescrape them")
    parser.add_argument("--url-file", default="data/investor_urls.txt", 
                        help="File with URLs to check")
    parser.add_argument("--no-proxy", action="store_true", 
                        help="Disable proxy usage")
    parser.add_argument("--limit", type=int, 
                        help="Limit number of URLs to rescrape")
    args = parser.parse_args()
    
    # Check if URL file exists, try legacy path if not
    if not os.path.exists(args.url_file):
        legacy_file = args.url_file.replace("data/", "output/")
        if os.path.exists(legacy_file):
            logger.info(f"Using legacy URL file: {legacy_file}")
            args.url_file = legacy_file
        else:
            logger.error(f"URL file not found: {args.url_file}")
            sys.exit(1)
    
    # Check for missing HTML files
    missing_urls = check_missing_html_files(args.url_file)
    
    if not missing_urls:
        logger.info("No missing HTML files found, all URLs have corresponding HTML files")
        return
    
    # Print missing URLs
    logger.info("Missing HTML files for the following URLs:")
    for i, url in enumerate(missing_urls[:10]):
        logger.info(f"  {i+1}. {url}")
    
    if len(missing_urls) > 10:
        logger.info(f"  ... and {len(missing_urls) - 10} more")
    
    # Prompt for confirmation
    print(f"\nFound {len(missing_urls)} missing HTML files. Proceed with rescraping? (y/n)")
    response = input("> ").strip().lower()
    
    if response != 'y':
        logger.info("Rescraping cancelled by user")
        return
    
    # Rescrape missing files
    success = rescrape_missing_files(missing_urls, not args.no_proxy, args.limit)
    
    if success:
        logger.info("All missing HTML files have been rescrapped successfully")
    else:
        logger.error("Some errors occurred during rescraping")
        sys.exit(1)

if __name__ == "__main__":
    main() 