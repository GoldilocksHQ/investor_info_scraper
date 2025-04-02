#!/usr/bin/env python

import os
import logging
import argparse
import time
import random
from urllib.parse import urlparse, urlunparse
from pathlib import Path

from src.investor_parser.core.scraper import ProxyManager, BasicScraper, BrowserScraper
from src.investor_parser.core.queue.url_queue import URLQueue

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/scraping.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs("data/html", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def get_output_filename(url: str, name: str) -> str:
    """
    Generate an output filename for the HTML content.
    
    Args:
        url: The URL of the investor profile
        name: The investor name or identifier
        
    Returns:
        Path to save the HTML content
    """
    # Extract the slug from the URL
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    
    if path_parts and path_parts[-1].startswith('investors-'):
        # Use the slug from the URL
        filename = f"{path_parts[-1]}.html"
    else:
        # Fallback to a sanitized name
        safe_name = name.lower().replace(' ', '-')
        filename = f"investors-{safe_name}.html"
    
    return os.path.join("data/html", filename)

def process_url(url: str, name: str, proxy_manager: ProxyManager, min_delay: float = None, max_delay: float = None) -> str:
    """
    Process a single URL:
    1. Try basic scraper first
    2. If dynamic content detected, use browser automation
    3. Save HTML content
    
    Args:
        url: URL to process
        name: Investor name or identifier
        proxy_manager: Proxy manager instance
        min_delay: Minimum delay between requests in seconds
        max_delay: Maximum delay between requests in seconds
        
    Returns:
        Path to saved HTML file or None if failed
    """
    logger.info(f"Processing URL: {url} ({name})")
    
    # Standardize the URL
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    # Create basic scraper with custom delays if specified
    basic_scraper_kwargs = {"proxy_manager": proxy_manager}
    if min_delay is not None and max_delay is not None:
        basic_scraper_kwargs["min_delay"] = min_delay
        basic_scraper_kwargs["max_delay"] = max_delay
    
    basic_scraper = BasicScraper(**basic_scraper_kwargs)
    
    # Try basic scraping first
    html_content, needs_browser = basic_scraper.fetch(url)
    
    # If basic scraping failed or needs browser automation
    if html_content is None or needs_browser:
        if html_content is None:
            logger.warning(f"Basic scraping failed for {url}, trying browser automation")
        else:
            logger.info(f"Dynamic content detected, switching to browser automation")
            
        # Create browser scraper with custom delays if specified
        browser_scraper_kwargs = {"proxy_manager": proxy_manager}
        if min_delay is not None and max_delay is not None:
            browser_scraper_kwargs["min_delay"] = min_delay
            browser_scraper_kwargs["max_delay"] = max_delay
        
        browser_scraper = BrowserScraper(**browser_scraper_kwargs)
        
        # Fetch using browser automation
        html_content = browser_scraper.fetch(url)
        
        if html_content is None:
            logger.error(f"Browser automation failed for {url}")
            return None
    
    # Save HTML content
    output_path = get_output_filename(url, name)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Saved HTML content to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving HTML content: {str(e)}")
        return None

def main():
    """
    Main function for the scraper script.
    """
    parser = argparse.ArgumentParser(description="Scrape investor profiles")
    parser.add_argument("--url-file", default="data/investor_urls.txt", help="File with URLs to scrape")
    parser.add_argument("--no-proxy", action="store_true", help="Disable proxy usage")
    parser.add_argument("--limit", type=int, help="Limit number of URLs to process")
    parser.add_argument("--min-delay", type=float, help="Minimum delay between requests in seconds")
    parser.add_argument("--max-delay", type=float, help="Maximum delay between requests in seconds")
    args = parser.parse_args()
    
    # Validate delay parameters if both are provided
    if (args.min_delay is not None and args.max_delay is None) or (args.min_delay is None and args.max_delay is not None):
        logger.error("Both --min-delay and --max-delay must be provided together")
        return
    
    if args.min_delay is not None and args.max_delay is not None and args.min_delay > args.max_delay:
        logger.error("--min-delay cannot be greater than --max-delay")
        return
    
    # Migrate URL file if needed
    if not os.path.exists(args.url_file) and os.path.exists("output/investor_urls.txt"):
        logger.info(f"Migrating URL file from output/investor_urls.txt to {args.url_file}")
        os.makedirs(os.path.dirname(args.url_file), exist_ok=True)
        with open("output/investor_urls.txt", "r", encoding="utf-8") as src, \
             open(args.url_file, "w", encoding="utf-8") as dst:
            dst.write(src.read())
    
    # Initialize components
    proxy_manager = ProxyManager(use_proxies=not args.no_proxy)
    url_queue = URLQueue()
    
    # Add URLs from file
    url_count = url_queue.add_urls_from_file(args.url_file)
    logger.info(f"Added {url_count} URLs to the queue")
    
    # Get queue statistics
    stats = url_queue.get_statistics()
    logger.info(f"Queue statistics: {stats}")
    
    # Process URLs
    processed_count = 0
    while True:
        # Check if we've reached the limit
        if args.limit and processed_count >= args.limit:
            logger.info(f"Reached limit of {args.limit} URLs")
            break
            
        # Get next URL
        result = url_queue.get_next_url()
        if result is None:
            logger.info("No more URLs to process")
            break
            
        item, index = result
        
        # Update status to in_progress
        url_queue.update_status(index, "in_progress")
        
        try:
            # Process URL with custom delays if specified
            output_path = process_url(
                item.url, 
                item.name, 
                proxy_manager,
                min_delay=args.min_delay,
                max_delay=args.max_delay
            )
            
            if output_path:
                # Update status to completed
                url_queue.update_status(index, "completed", output_path=output_path)
                processed_count += 1
            else:
                # Update status to failed
                url_queue.update_status(index, "failed", error_message="Failed to process URL")
                
        except Exception as e:
            # Update status to failed
            url_queue.update_status(index, "failed", error_message=str(e))
            logger.exception(f"Error processing URL {item.url}: {str(e)}")
            
        # Get updated statistics
        stats = url_queue.get_statistics()
        logger.info(f"Queue statistics: {stats}")
        
        # Random delay between URLs (using custom delays if specified)
        min_d = args.min_delay if args.min_delay is not None else 3
        max_d = args.max_delay if args.max_delay is not None else 8
        delay = random.uniform(min_d, max_d)
        logger.info(f"Waiting {delay:.2f} seconds before next URL...")
        time.sleep(delay)
    
    # Final statistics
    stats = url_queue.get_statistics()
    logger.info(f"Final queue statistics: {stats}")
    logger.info(f"Processed {processed_count} URLs")
    
if __name__ == "__main__":
    main() 