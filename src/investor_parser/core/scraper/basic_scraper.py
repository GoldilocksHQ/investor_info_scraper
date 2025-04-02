#!/usr/bin/env python

import time
import random
import requests
import logging
from typing import Dict, Optional, Tuple, List
from bs4 import BeautifulSoup

from src.investor_parser.core.scraper.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class BasicScraper:
    """
    A simple scraper using the requests library for fetching static HTML content.
    """
    
    def __init__(
        self, 
        proxy_manager: Optional[ProxyManager] = None,
        user_agents: Optional[List[str]] = None,
        retry_count: int = 3,
        timeout: int = 30,
        min_delay: float = 3.0,
        max_delay: float = 8.0
    ):
        """
        Initialize the basic scraper.
        
        Args:
            proxy_manager: Optional proxy manager for using proxies
            user_agents: List of user agent strings to rotate
            retry_count: Number of retries for failed requests
            timeout: Request timeout in seconds
            min_delay: Minimum delay between requests in seconds
            max_delay: Maximum delay between requests in seconds
        """
        self.proxy_manager = proxy_manager or ProxyManager(use_proxies=False)
        self.user_agents = user_agents or [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]
        self.retry_count = retry_count
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        
    def get_random_user_agent(self) -> str:
        """
        Get a random user agent from the list.
        
        Returns:
            A random user agent string
        """
        return random.choice(self.user_agents)
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get request headers with a random user agent.
        
        Returns:
            Dictionary with request headers
        """
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
    def needs_browser_automation(self, html_content: str) -> bool:
        """
        Check if the page requires browser automation.
        
        Args:
            html_content: HTML content to check
            
        Returns:
            True if browser automation is needed, False otherwise
        """
        # Look for "See all investments" button
        soup = BeautifulSoup(html_content, 'html.parser')
        see_all_button = soup.find(string=lambda text: text and 'See all' in text and 'investments on record' in text.lower())
        
        return see_all_button is not None
        
    def fetch(self, url: str) -> Tuple[Optional[str], bool]:
        """
        Fetch HTML content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (HTML content or None if failed, needs_browser_automation flag)
        """
        for attempt in range(self.retry_count):
            try:
                # Random delay between requests
                if attempt > 0:
                    delay = random.uniform(self.min_delay * (attempt + 1), self.max_delay * (attempt + 1))
                    logger.info(f"Retry {attempt+1}/{self.retry_count}, waiting {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    time.sleep(random.uniform(self.min_delay, self.max_delay))
                
                logger.info(f"Fetching URL: {url}")
                proxies = self.proxy_manager.get_proxy_dict() if self.proxy_manager.is_enabled() else {}
                
                response = requests.get(
                    url,
                    headers=self.get_headers(),
                    proxies=proxies,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                # Check if we got a valid response
                html_content = response.text
                if not html_content or len(html_content) < 1000:
                    logger.warning(f"Received suspiciously small HTML ({len(html_content)} bytes)")
                    continue
                    
                # Check if we need browser automation
                needs_automation = self.needs_browser_automation(html_content)
                if needs_automation:
                    logger.info(f"Detected 'See all investments' button, needs browser automation")
                
                return html_content, needs_automation
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt == self.retry_count - 1:
                    logger.error(f"Max retries reached for {url}")
                    return None, False
        
        return None, False 