#!/usr/bin/env python

import os
import logging
import argparse
import subprocess
import sys
import re
import glob
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/process_all.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs("data/html", exist_ok=True)
os.makedirs("data/output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def run_scraper(url_file: str, limit: int = None, use_proxy: bool = True, min_delay: float = None, max_delay: float = None) -> bool:
    """
    Run the scraper script to download HTML files.
    
    Args:
        url_file: Path to file with URLs to scrape
        limit: Maximum number of URLs to process
        use_proxy: Whether to use proxies
        min_delay: Minimum delay between requests in seconds
        max_delay: Maximum delay between requests in seconds
        
    Returns:
        True if scraping was successful, False otherwise
    """
    logger.info(f"Starting scraping process from {url_file}")
    
    cmd = [sys.executable, "-m", "src.investor_parser.scripts.scrape_profiles", "--url-file", url_file]
    
    if limit:
        cmd.extend(["--limit", str(limit)])
    
    if not use_proxy:
        cmd.append("--no-proxy")
    
    if min_delay is not None:
        cmd.extend(["--min-delay", str(min_delay)])
    
    if max_delay is not None:
        cmd.extend(["--max-delay", str(max_delay)])
        
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logger.info("Scraping completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Scraping failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logger.exception(f"Error running scraper: {str(e)}")
        return False

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

def run_scraper_for_missing_files(url_file: str, missing_urls: list, use_proxy: bool = True, min_delay: float = None, max_delay: float = None) -> bool:
    """
    Run the scraper specifically for missing HTML files.
    
    Args:
        url_file: Original URL file path (for logging purposes)
        missing_urls: List of URLs to scrape
        use_proxy: Whether to use proxies
        min_delay: Minimum delay between requests in seconds
        max_delay: Maximum delay between requests in seconds
        
    Returns:
        True if scraping was successful, False otherwise
    """
    if not missing_urls:
        return True
    
    logger.info(f"Scraping {len(missing_urls)} missing HTML files")
    
    # Create a temporary file with the missing URLs
    temp_url_file = "data/missing_urls.txt"
    with open(temp_url_file, "w", encoding="utf-8") as f:
        for url in missing_urls:
            f.write(f"{url}\n")
    
    # Run the scraper with the temporary file
    cmd = [sys.executable, "-m", "src.investor_parser.scripts.scrape_profiles", "--url-file", temp_url_file]
    
    if not use_proxy:
        cmd.append("--no-proxy")
    
    if min_delay is not None:
        cmd.extend(["--min-delay", str(min_delay)])
    
    if max_delay is not None:
        cmd.extend(["--max-delay", str(max_delay)])
        
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

def run_parser() -> bool:
    """
    Run the parser to process HTML files.
    
    Returns:
        True if parsing was successful, False otherwise
    """
    logger.info("Starting parsing process")
    
    cmd = [sys.executable, "-m", "src.investor_parser.scripts.parse_all"]
    
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logger.info("Parsing completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Parsing failed with exit code {e.returncode}")
        return False
    except Exception as e:
        logger.exception(f"Error running parser: {str(e)}")
        return False

def main():
    """
    Main function to run the end-to-end process.
    """
    parser = argparse.ArgumentParser(description="Process investor profiles end-to-end")
    parser.add_argument("--url-file", default="data/investor_urls.txt", help="File with URLs to scrape")
    parser.add_argument("--no-proxy", action="store_true", help="Disable proxy usage")
    parser.add_argument("--limit", type=int, help="Limit number of URLs to process")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip scraping and only run parsing")
    parser.add_argument("--skip-parse", action="store_true", help="Skip parsing and only run scraping")
    parser.add_argument("--check-missing", action="store_true", help="Check and rescrape missing HTML files")
    parser.add_argument("--min-delay", type=float, help="Minimum delay between requests in seconds")
    parser.add_argument("--max-delay", type=float, help="Maximum delay between requests in seconds")
    args = parser.parse_args()
    
    # Validate delay parameters if both are provided
    if (args.min_delay is not None and args.max_delay is None) or (args.min_delay is None and args.max_delay is not None):
        logger.error("Both --min-delay and --max-delay must be provided together")
        return False
    
    if args.min_delay is not None and args.max_delay is not None and args.min_delay > args.max_delay:
        logger.error("--min-delay cannot be greater than --max-delay")
        return False
    
    success = True
    
    # Migrate old URL file if needed
    if not os.path.exists(args.url_file) and os.path.exists("output/investor_urls.txt"):
        logger.info("Migrating URL file from 'output/investor_urls.txt' to 'data/investor_urls.txt'")
        os.makedirs(os.path.dirname(args.url_file), exist_ok=True)
        with open("output/investor_urls.txt", "r", encoding="utf-8") as src, \
             open(args.url_file, "w", encoding="utf-8") as dst:
            dst.write(src.read())
    
    # Check for missing files
    if args.check_missing or not args.skip_scrape:
        missing_urls = check_missing_html_files(args.url_file)
        if missing_urls and not args.skip_scrape:
            run_scraper_for_missing_files(
                args.url_file, 
                missing_urls, 
                not args.no_proxy,
                min_delay=args.min_delay,
                max_delay=args.max_delay
            )
    
    # Run scraper unless skipped
    if not args.skip_scrape:
        success = run_scraper(
            args.url_file, 
            args.limit, 
            not args.no_proxy,
            min_delay=args.min_delay,
            max_delay=args.max_delay
        )
        if not success and not args.skip_parse:
            logger.warning("Scraping failed, but continuing with parsing")
    
    # Run parser unless skipped
    if not args.skip_parse:
        success = run_parser() and success
    
    if success:
        logger.info("End-to-end processing completed successfully")
    else:
        logger.error("End-to-end processing completed with errors")
        sys.exit(1)

if __name__ == "__main__":
    main() 