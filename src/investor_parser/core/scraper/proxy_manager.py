#!/usr/bin/env python

import random
import logging
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    Manages proxy configuration for web scraping operations.
    Supports both requests library and Playwright.
    """
    
    def __init__(self, use_proxies: bool = True):
        """
        Initialize the proxy manager.
        
        Args:
            use_proxies: Whether to use proxies for requests
        """
        self.use_proxies = use_proxies
        self.username = 'gWQ2Gtskb5n1QnPf'
        self.password = 'j6vVHUjqfKyNr66Y_streaming-1'
        self.proxy_host = 'geo.iproyal.com'
        self.proxy_port = '12321'
        
    def get_proxy_url(self) -> Optional[str]:
        """
        Get a formatted proxy URL for the requests library.
        
        Returns:
            Proxy URL string or None if proxies are disabled
        """
        if not self.use_proxies:
            return None
            
        auth = f"{self.username}:{self.password}"
        return f"http://{auth}@{self.proxy_host}:{self.proxy_port}"
        
    def get_proxy_dict(self) -> Dict[str, str]:
        """
        Get a proxy dictionary for the requests library.
        
        Returns:
            Dictionary with proxy configuration
        """
        if not self.use_proxies:
            return {}
            
        proxy_url = self.get_proxy_url()
        return {
            "http": proxy_url,
            "https": proxy_url
        }
        
    def get_playwright_proxy(self) -> Dict[str, Any]:
        """
        Get a proxy configuration for Playwright.
        
        Returns:
            Dictionary with Playwright proxy configuration
        """
        if not self.use_proxies:
            return {}
            
        return {
            "server": f"http://{self.proxy_host}:{self.proxy_port}",
            "username": self.username,
            "password": self.password
        }
        
    def is_enabled(self) -> bool:
        """
        Check if proxy usage is enabled.
        
        Returns:
            True if proxies are enabled, False otherwise
        """
        return self.use_proxies 