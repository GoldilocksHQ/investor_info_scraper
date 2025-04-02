"""
Scraping components for investor profile data extraction.
"""

from src.investor_parser.core.scraper.proxy_manager import ProxyManager
from src.investor_parser.core.scraper.basic_scraper import BasicScraper
from src.investor_parser.core.scraper.browser_scraper import BrowserScraper

__all__ = ['ProxyManager', 'BasicScraper', 'BrowserScraper'] 