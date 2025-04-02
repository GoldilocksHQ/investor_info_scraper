#!/usr/bin/env python
"""
End-to-end test script for investor profile scraping and parsing workflow.

This script:
1. Takes a sample of investor URLs from the investor_urls.txt file
2. Scrapes each URL with anti-detection and investment expansion
3. Parses the downloaded HTML
4. Validates that investments were properly expanded
5. Produces a summary report

Usage:
    python test_flow.py [--sample n] [--headless] [--browser {chromium,firefox,webkit}]
"""

import os
import sys
import time
import logging
import argparse
import json
import random
from pathlib import Path
from typing import List, Dict, Any

# Set up path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import scraping and parsing components
from src.investor_parser.core.scraper import ProxyManager, BrowserScraper
from src.investor_parser.core.parser import InvestorProfileParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/flow_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs("data/html", exist_ok=True)
os.makedirs("data/output", exist_ok=True)
os.makedirs("data/screenshots", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def get_urls_from_file(filepath: str, sample_size: int = None) -> List[str]:
    """
    Get URLs from file, optionally taking a random sample.
    
    Args:
        filepath: Path to the file containing URLs
        sample_size: Number of URLs to sample (None for all)
        
    Returns:
        List of URLs
    """
    # Always include Mark Cuban as we know he has investments
    known_profiles = ["https://signal.nfx.com/investors/mark-cuban"]
    
    if not os.path.exists(filepath):
        logger.error(f"URL file not found: {filepath}")
        return known_profiles
    
    with open(filepath, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Found {len(urls)} URLs in {filepath}")
    
    if sample_size and sample_size < len(urls):
        # Sample some random URLs excluding known profiles that might already be in the file
        random_urls = [url for url in urls if url not in known_profiles]
        sampled = random.sample(random_urls, min(sample_size - 1, len(random_urls)))
        # Add back known profiles
        sampled = known_profiles + sampled
        logger.info(f"Sampled {len(sampled)} URLs for testing")
        return sampled
    
    # Make sure known profiles are included
    for url in known_profiles:
        if url not in urls:
            urls.append(url)
    
    return urls

def get_output_filename(url: str) -> str:
    """
    Generate a filename for the output HTML file.
    
    Args:
        url: URL to process
        
    Returns:
        Output filename
    """
    # Extract the slug from the URL
    parts = url.strip('/').split('/')
    investor_name = parts[-1] if parts else "unknown"
    
    # Create filename
    return f"data/html/test-{investor_name}.html"

def process_url(url: str, browser_scraper: BrowserScraper) -> Dict[str, Any]:
    """
    Process a single URL: scrape and parse.
    
    Args:
        url: URL to process
        browser_scraper: BrowserScraper instance
        
    Returns:
        Dictionary with results
    """
    start_time = time.time()
    output_file = get_output_filename(url)
    
    result = {
        "url": url,
        "output_file": output_file,
        "success": False,
        "time_taken": 0,
        "investment_count": 0,
        "expanded": False,
        "error": None
    }
    
    try:
        logger.info(f"Processing URL: {url}")
        # Scrape the URL
        html_content = browser_scraper.fetch(url)
        
        if html_content:
            # Save HTML content
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Saved HTML to {output_file}")
            
            # Parse the investor profile
            parser = InvestorProfileParser(html_content, output_file)
            data = parser.parse()
            
            # Check investments
            investments = data.get('investments', [])
            result["investment_count"] = len(investments)
            
            # Check if expansion likely worked (heuristic)
            # A profile with more than 10 investments was likely expanded
            result["expanded"] = len(investments) > 10
            
            # Save parsed data
            investor_name = url.strip('/').split('/')[-1]
            output_json = f"data/output/flow-test-{investor_name}.json"
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            # Mark as success
            result["success"] = True
            logger.info(f"Found {len(investments)} investments for {investor_name}")
            
            if len(investments) > 0:
                # Print first few investments
                for i, inv in enumerate(investments[:3]):
                    logger.info(f"  {i+1}. {inv.get('company', 'Unknown')} - {inv.get('total_raised', 'Unknown')}")
        else:
            result["error"] = "Failed to fetch HTML content"
            logger.error(f"Failed to fetch HTML content for {url}")
    
    except Exception as e:
        result["error"] = str(e)
        logger.exception(f"Error processing URL {url}: {e}")
    
    result["time_taken"] = time.time() - start_time
    return result

def main():
    """Main function to run the flow test."""
    parser = argparse.ArgumentParser(description="Test end-to-end investor profile scraping and parsing")
    parser.add_argument("--sample", type=int, default=3, 
                        help="Number of URLs to sample (default: 3)")
    parser.add_argument("--headless", action="store_true", default=False,
                        help="Run in headless mode")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], 
                        default="firefox", help="Browser to use")
    args = parser.parse_args()
    
    # Get URLs to process
    urls = get_urls_from_file("data/investor_urls.txt", args.sample)
    if not urls:
        logger.error("No URLs to process")
        return
    
    # Initialize components
    proxy_manager = ProxyManager(use_proxies=False)
    browser_scraper = BrowserScraper(
        proxy_manager=proxy_manager,
        headless=args.headless,
        browser_type=args.browser,
        screenshot_dir="data/screenshots",
        stealth_mode=True,
        random_mouse_movements=True
    )
    
    # Process URLs
    results = []
    for url in urls:
        result = process_url(url, browser_scraper)
        results.append(result)
        
        # Add delay between URLs
        if url != urls[-1]:
            delay = random.uniform(5, 10)
            logger.info(f"Waiting {delay:.2f} seconds before next URL...")
            time.sleep(delay)
    
    # Generate summary
    success_count = sum(1 for r in results if r["success"])
    expanded_count = sum(1 for r in results if r["expanded"])
    avg_time = sum(r["time_taken"] for r in results) / len(results) if results else 0
    total_investments = sum(r["investment_count"] for r in results)
    
    # Save detailed results
    with open("data/output/flow_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n=== Flow Test Results ===")
    print(f"URLs processed: {len(results)}")
    print(f"Successful scrapes: {success_count}/{len(results)}")
    print(f"Profiles with expanded investments: {expanded_count}/{len(results)}")
    print(f"Total investments found: {total_investments}")
    print(f"Average time per URL: {avg_time:.2f} seconds")
    print(f"Detailed results saved to: data/output/flow_test_results.json")

if __name__ == "__main__":
    main() 