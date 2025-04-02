#!/usr/bin/env python

import time
import random
import logging
import asyncio
import json
from typing import Optional, Dict, Any, List, Tuple
import os
import platform
from pathlib import Path

# Import Playwright - we'll handle the import errors gracefully
try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Route, Request
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from src.investor_parser.core.scraper.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class BrowserScraper:
    """
    A browser automation scraper using Playwright to handle JavaScript-rendered content.
    Enhanced with anti-detection features.
    """
    
    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        user_agents: Optional[List[str]] = None,
        headless: bool = True,
        browser_type: str = "chromium",
        screenshot_dir: Optional[str] = "data/screenshots",
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        timeout: int = 60000,  # milliseconds
        stealth_mode: bool = True,
        random_mouse_movements: bool = True
    ):
        """
        Initialize the browser scraper with anti-detection features.
        
        Args:
            proxy_manager: Optional proxy manager for using proxies
            user_agents: List of user agent strings to rotate
            headless: Whether to run browser in headless mode
            browser_type: Browser to use (chromium, firefox, webkit)
            screenshot_dir: Directory to save screenshots
            min_delay: Minimum delay between actions in seconds
            max_delay: Maximum delay between actions in seconds
            timeout: Page navigation timeout in milliseconds
            stealth_mode: Enable stealth mode to avoid detection
            random_mouse_movements: Enable random mouse movements
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for browser automation. "
                "Install it with: pip install playwright && playwright install"
            )
            
        self.proxy_manager = proxy_manager or ProxyManager(use_proxies=False)
        
        # Enhanced list of modern user agents
        self.user_agents = user_agents or [
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            # Chrome on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
            # Safari on macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            # Edge on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.81',
            # Chrome on Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        ]
        
        # Configure headless mode (using headless=new for better detection avoidance)
        self.headless = headless  # Keep as boolean for Playwright 1.51.0
        self.browser_type = browser_type
        self.screenshot_dir = screenshot_dir
        
        # Use slightly larger range for more natural delays
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        
        # Anti-detection features
        self.stealth_mode = stealth_mode
        self.random_mouse_movements = random_mouse_movements
        
        # Initialize screenshot directory
        if self.screenshot_dir:
            os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def get_random_user_agent(self) -> str:
        """
        Get a random user agent from the list.
        
        Returns:
            A random user agent string
        """
        return random.choice(self.user_agents)
    
    def random_delay(self, multiplier: float = 1.0) -> None:
        """
        Sleep for a random amount of time with natural variation.
        
        Args:
            multiplier: Multiplier for the delay range
        """
        # Add small random component for more natural timing
        base_delay = random.uniform(self.min_delay * multiplier, self.max_delay * multiplier)
        # Add small variation (0-300ms) to make delays look more human
        natural_variation = random.uniform(0, 0.3)
        delay = base_delay + natural_variation
        
        logger.info(f"Waiting for {delay:.2f} seconds...")
        time.sleep(delay)
    
    def get_browser_fingerprint(self) -> Dict[str, Any]:
        """
        Generate a realistic browser fingerprint.
        
        Returns:
            Dictionary with browser fingerprint data
        """
        # Generate a consistent but random fingerprint
        operating_systems = {
            'Windows': ['10', '11'],
            'Macintosh': ['10.15', '11.0', '12.0', '13.0', '14.0'],
            'Linux': ['x86_64', 'i686']
        }
        
        os_name = random.choice(list(operating_systems.keys()))
        os_version = random.choice(operating_systems[os_name])
        
        # WebGL info
        webgl_vendors = ['Google Inc.', 'Intel Inc.', 'NVIDIA Corporation', 'ATI Technologies Inc.']
        webgl_renderers = [
            'ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0)',
            'ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0)',
            'ANGLE (AMD, AMD Radeon Pro 5500M OpenGL Engine, OpenGL 4.1)',
            'Mesa DRI Intel(R) UHD Graphics 620 (KBL GT2)'
        ]
        
        return {
            'userAgent': self.get_random_user_agent(),
            'platform': os_name,
            'oscpu': f'{os_name} {os_version}',
            'hardwareConcurrency': random.randint(4, 16),
            'deviceMemory': random.choice([2, 4, 8, 16]),
            'webgl': {
                'vendor': random.choice(webgl_vendors),
                'renderer': random.choice(webgl_renderers),
            },
            'language': random.choice(['en-US', 'en-GB', 'en-CA', 'en-AU']),
            'timezone': random.choice(['America/New_York', 'America/Los_Angeles', 'Europe/London', 'Asia/Tokyo']),
            'screenResolution': random.choice([[1920, 1080], [2560, 1440], [1366, 768], [1440, 900], [3840, 2160]]),
        }
    
    async def bypass_fingerprinting(self, page: Page) -> None:
        """
        Apply anti-fingerprinting techniques to the page.
        
        Args:
            page: Playwright page instance
        """
        fingerprint = self.get_browser_fingerprint()
        
        # Override JavaScript properties commonly used for fingerprinting
        await page.evaluate("""
            (fingerprint) => {
                // Override navigator properties
                const navigatorProps = {
                    userAgent: fingerprint.userAgent,
                    platform: fingerprint.platform,
                    hardwareConcurrency: fingerprint.hardwareConcurrency,
                    deviceMemory: fingerprint.deviceMemory,
                    language: fingerprint.language,
                    languages: [fingerprint.language],
                };
                
                for (const [key, value] of Object.entries(navigatorProps)) {
                    if (value !== undefined) {
                        Object.defineProperty(navigator, key, {
                            get: () => value,
                            configurable: true
                        });
                    }
                }
                
                // Override screen properties
                if (fingerprint.screenResolution) {
                    Object.defineProperty(screen, 'width', { get: () => fingerprint.screenResolution[0] });
                    Object.defineProperty(screen, 'height', { get: () => fingerprint.screenResolution[1] });
                    Object.defineProperty(screen, 'availWidth', { get: () => fingerprint.screenResolution[0] });
                    Object.defineProperty(screen, 'availHeight', { get: () => fingerprint.screenResolution[1] });
                }
                
                // Override timezone
                if (fingerprint.timezone) {
                    Intl.DateTimeFormat = new Proxy(Intl.DateTimeFormat, {
                        construct(target, args) {
                            const options = args[1] || {};
                            if (!options.timeZone) {
                                options.timeZone = fingerprint.timezone;
                                args[1] = options;
                            }
                            return Reflect.construct(target, args);
                        }
                    });
                }
                
                // Block known fingerprinting methods
                const block = () => { return { id: 1, random: () => 0.1234 }; };
                window.RTCPeerConnection = block;
                window.RTCSessionDescription = block;
                window.AudioContext = block;
                window.OfflineAudioContext = block;
            }
        """, fingerprint)
    
    async def apply_stealth_patches(self, page: Page) -> None:
        """
        Apply stealth patches to avoid common detection methods.
        
        Args:
            page: Playwright page instance
        """
        # Mask WebDriver and Playwright-specific properties
        await page.evaluate("""
            () => {
                // Remove webdriver property
                delete Object.getPrototypeOf(navigator).webdriver;
                
                // Patch Chrome's permissions API
                if (navigator.permissions) {
                    const originalQuery = navigator.permissions.query;
                    navigator.permissions.query = function(parameters) {
                        if (parameters.name === 'notifications' || parameters.name === 'clipboard-read') {
                            return Promise.resolve({ state: "prompt", onchange: null });
                        }
                        return originalQuery.call(this, parameters);
                    };
                }
                
                // Add plugins array (empty arrays are suspicious)
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const plugins = [
                            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                            { name: 'Native Client', filename: 'internal-nacl-plugin' }
                        ];
                        plugins.item = idx => plugins[idx];
                        plugins.namedItem = name => plugins.find(p => p.name === name);
                        plugins.refresh = () => {};
                        plugins.length = plugins.length;
                        return plugins;
                    }
                });
                
                // Fix dimensions (0x0 iframes are suspicious)
                Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                    get: function() {
                        const win = this.contentDocument.defaultView;
                        try {
                            win.self = win;
                            win.frameElement = this;
                        } catch (e) {}
                        return win;
                    }
                });
            }
        """)
    
    async def simulate_human_behavior(self, page: Page) -> None:
        """
        Simulate human-like behavior on the page.
        
        Args:
            page: Playwright page instance
        """
        # Random scroll behavior
        scroll_distance = random.randint(100, 800)
        scroll_steps = random.randint(3, 8)
        
        for step in range(scroll_steps):
            # Gradually scroll down with variable speed
            await page.mouse.wheel(
                delta_x=0, 
                delta_y=scroll_distance // scroll_steps * random.uniform(0.8, 1.2)
            )
            # Small pause between scrolls
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        if self.random_mouse_movements:
            # Perform some random mouse movements
            viewportSize = await page.evaluate("""() => {
                return { width: window.innerWidth, height: window.innerHeight }
            }""")
            
            width = viewportSize.get('width', 1200)
            height = viewportSize.get('height', 800)
            
            # Random mouse movements
            moves = random.randint(2, 5)
            for _ in range(moves):
                x = random.randint(100, width - 200)
                y = random.randint(100, height - 200)
                # Move mouse with variable speed
                await page.mouse.move(x, y, steps=random.randint(5, 15))
                await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def intercept_bot_checks(self, page: Page) -> None:
        """
        Set up request interception to modify headers and responses for bypassing bot checks.
        
        Args:
            page: Playwright page instance
        """
        # Add headers that regular browsers typically include
        await page.route("**/*", lambda route: self._add_realistic_headers(route))
        
        # Intercept requests for common bot detection scripts
        detection_patterns = [
            "*datadome*", 
            "*botdetect*", 
            "*cloudflare*", 
            "*captcha*", 
            "*recaptcha*",
            "*fingerprint*", 
            "*distil*", 
            "*imperva*",
            "*perimeterx*"
        ]
        
        for pattern in detection_patterns:
            await page.route(pattern, lambda route: self._handle_detection_script(route))
    
    async def _add_realistic_headers(self, route: Route) -> None:
        """
        Add realistic headers to requests.
        
        Args:
            route: Playwright route
        """
        request = route.request
        headers = {**request.headers}
        
        # Add common browser headers
        headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        })
        
        # Continue with modified headers
        await route.continue_(headers=headers)
    
    async def _handle_detection_script(self, route: Route) -> None:
        """
        Handle bot detection scripts by either blocking or modifying them.
        
        Args:
            route: Playwright route
        """
        # Strategy depends on the request
        request_url = route.request.url.lower()
        
        if 'captcha' in request_url or 'recaptcha' in request_url:
            # For captcha requests, it's often better to let them load but modify behavior
            await route.continue_()
        elif any(detector in request_url for detector in ['datadome', 'distil', 'imperva', 'perimeterx']):
            # For known bot detectors, we can either:
            if random.random() > 0.3:  # 70% of the time let it load with delays
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await route.continue_()
            else:  # 30% of the time abort or modify
                # Abort with a realistic error
                await route.abort("internetdisconnected")
        else:
            # Default to continuing for unknown patterns
            await route.continue_()
            
    async def setup_browser(self) -> Tuple[Any, Browser, BrowserContext]:
        """
        Set up a browser instance with the appropriate configuration.
        
        Returns:
            Tuple of (playwright instance, browser instance, browser context)
        """
        playwright = await async_playwright().start()
        
        # Set up advanced browser launch options
        launch_options = {
            "headless": self.headless,
            "args": [
                # Disable automation flags
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                # Disable GPU to avoid detection
                '--disable-gpu',
                # Randomize window size slightly
                f'--window-size={random.randint(1280, 1366)},{random.randint(800, 900)}',
                # Add language
                '--lang=en-US,en',
                # Disable password saving popup
                '--disable-save-password-bubble',
                # Disable notifications
                '--disable-notifications'
            ]
        }
        
        # Different browser types need different configurations
        if self.browser_type == 'chromium':
            launch_options['args'].extend([
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--no-default-browser-check',
                '--no-first-run',
                '--disable-default-apps'
            ])
        
        # Set up browser context options with realistic profile
        context_options = {
            "user_agent": self.get_random_user_agent(),
            "viewport": {
                "width": random.randint(1280, 1920),
                "height": random.randint(800, 1080)
            },
            "screen": {
                "width": random.randint(1280, 1920),
                "height": random.randint(800, 1080)
            },
            "device_scale_factor": random.choice([1, 1.5, 2]),
            "is_mobile": False,
            "has_touch": random.choice([True, False]),
            "locale": random.choice(["en-US", "en-GB", "en-CA"]),
            "timezone_id": random.choice(["America/New_York", "America/Los_Angeles", "Europe/London"]),
            "ignore_https_errors": True,
            "java_script_enabled": True,
            # Emulate real storage
            "storage_state": {
                "cookies": [],
                "origins": []
            },
            # Add geolocation permission
            "permissions": ["geolocation"],
        }
        
        # Add proxy if enabled
        if self.proxy_manager.is_enabled():
            context_options["proxy"] = self.proxy_manager.get_playwright_proxy()
            
        # Launch browser
        if self.browser_type == "firefox":
            browser = await playwright.firefox.launch(**launch_options)
        elif self.browser_type == "webkit":
            browser = await playwright.webkit.launch(**launch_options)
        else:
            browser = await playwright.chromium.launch(**launch_options)
            
        # Create context
        context = await browser.new_context(**context_options)
        
        # Set default timeout
        context.set_default_timeout(self.timeout)
        
        return playwright, browser, context
        
    async def take_screenshot(self, page: Page, name: str) -> Optional[str]:
        """
        Take a screenshot of the current page.
        
        Args:
            page: Playwright page instance
            name: Name for the screenshot file
            
        Returns:
            Path to the screenshot or None if screenshot_dir is not set
        """
        if not self.screenshot_dir:
            return None
            
        filepath = os.path.join(self.screenshot_dir, f"{name}_{int(time.time())}.png")
        await page.screenshot(path=filepath, full_page=True)
        logger.info(f"Screenshot saved to {filepath}")
        return filepath
        
    async def expand_investments(self, page: Page) -> bool:
        """
        Find and click the "See all investments" button if present.
        Uses multiple approaches including direct JavaScript for reliability.
        
        Args:
            page: Playwright page instance
            
        Returns:
            True if button was found and clicked, False otherwise
        """
        try:
            # First take a screenshot before trying to find the button
            await self.take_screenshot(page, "before_expand")
            
            # APPROACH 1: Use direct JavaScript to find and click the button
            # This is the most reliable approach as it doesn't depend on specific selectors
            button_clicked = await page.evaluate("""() => {
                try {
                    // Various possible button text patterns
                    const buttonTexts = [
                        'See all investments',
                        'See all investments on record',
                        'See all',
                        'View all investments',
                        'Show more investments'
                    ];
                    
                    // Find all buttons/links in the page
                    const allElements = Array.from(document.querySelectorAll('button, a, [role="button"], .button, [class*="button"]'));
                    
                    // Find elements containing our target text
                    for (const text of buttonTexts) {
                        const elements = allElements.filter(el => 
                            el.textContent && 
                            el.textContent.toLowerCase().includes(text.toLowerCase())
                        );
                        
                        if (elements.length > 0) {
                            // Log what we found
                            console.log('Found button with text: ' + elements[0].textContent.trim());
                            
                            // Make the element more visible for screenshots
                            elements[0].style.border = '3px solid red';
                            
                            // Check if button is in viewport
                            const rect = elements[0].getBoundingClientRect();
                            if (rect.bottom < 0 || rect.top > window.innerHeight) {
                                // Scroll element into view if not visible
                                elements[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                                // Wait a bit for scroll to complete
                                setTimeout(() => {
                                    elements[0].click();
                                }, 500);
                                return true;
                            }
                            
                            // Click the button using JavaScript
                            elements[0].click();
                            return true;
                        }
                    }
                    
                    // Try more generic approach for buttons near investment lists
                    const tableHeaders = Array.from(document.querySelectorAll('thead th, table th'));
                    const investmentHeader = tableHeaders.find(el => 
                        el.textContent && el.textContent.includes('Investment')
                    );
                    
                    if (investmentHeader) {
                        // Look for buttons near this table
                        const table = investmentHeader.closest('table');
                        if (table) {
                            const tableContainer = table.parentElement;
                            const buttons = Array.from(tableContainer.querySelectorAll('button, a, [role="button"]'));
                            if (buttons.length > 0) {
                                console.log('Found button near investment table: ' + buttons[0].textContent.trim());
                                buttons[0].style.border = '3px solid red';
                                buttons[0].click();
                                return true;
                            }
                        }
                    }
                    
                    // Last resort: look for sections containing "Investments"
                    const sections = Array.from(document.querySelectorAll('div, section'));
                    const investmentSections = sections.filter(el => 
                        el.textContent && (
                            el.textContent.includes('Investments') || 
                            el.textContent.includes('Portfolio') ||
                            el.textContent.includes('Companies funded')
                        )
                    );
                    
                    if (investmentSections.length > 0) {
                        for (const section of investmentSections) {
                            const buttons = Array.from(section.querySelectorAll('button, a, [role="button"]'));
                            if (buttons.length > 0) {
                                console.log('Found button in investment section: ' + buttons[0].textContent.trim());
                                buttons[0].style.border = '3px solid red';
                                buttons[0].click();
                                return true;
                            }
                        }
                    }
                    
                    return false;
                } catch (e) {
                    console.error('Error in JS button finder:', e);
                    return false;
                }
            }""")
            
            if button_clicked:
                logger.info("Found and clicked 'See all investments' button using JavaScript")
                
                # Wait for network activity after JavaScript click
                await page.wait_for_load_state("networkidle")
                
                # Extra wait for dynamic content
                await asyncio.sleep(random.uniform(2.0, 3.5))
                
                # Take another screenshot after expansion
                await self.take_screenshot(page, "after_expand")
                return True
                
            # APPROACH 2: If JavaScript approach failed, try with Playwright selectors
            # Try multiple selector strategies to find the "See all investments" button
            button_found = False
            button = None
            
            # Strategy 1: Look for button with specific text content
            button_selectors = [
                "button:has-text('See all investments')",
                "button:has-text('See all')",
                "text=See all investments",
                "[role='button']:has-text('See all investments')",
                "[role='button']:has-text('See all')",
                "a:has-text('See all investments')",
                "a:has-text('See all')"
            ]
            
            for selector in button_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0:
                        logger.info(f"Found button using selector: {selector}")
                        button_found = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {str(e)}")
                    continue
            
            # Strategy 2: Look by XPath if previous selectors failed
            if not button_found:
                xpath_selectors = [
                    "//button[contains(., 'See all investments')]",
                    "//button[contains(., 'See all')]",
                    "//*[contains(@class, 'button') and contains(text(), 'See all')]",
                    "//*[contains(text(), 'See all investments')]",
                    "//a[contains(text(), 'See all investments')]"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        button = page.locator(xpath)
                        if await button.count() > 0:
                            logger.info(f"Found button using XPath: {xpath}")
                            button_found = True
                            break
                    except Exception as e:
                        logger.debug(f"XPath {xpath} failed: {str(e)}")
                        continue
            
            # If button exists, click it with human-like behavior
            if button_found and button:
                logger.info("Found 'See all investments' button, clicking...")
                
                # Random delay before clicking to look human
                self.random_delay()
                
                # Try to get button position for natural click
                try:
                    # First scroll to make sure it's in view
                    await button.scroll_into_view_if_needed()
                    await asyncio.sleep(random.uniform(0.5, 1.0))
                    
                    button_box = await button.bounding_box()
                    if button_box:
                        # Move mouse to button with human-like motion
                        x = button_box['x'] + button_box['width'] / 2 + random.uniform(-5, 5)
                        y = button_box['y'] + button_box['height'] / 2 + random.uniform(-3, 3)
                        
                        # Move mouse to button with human-like motion
                        await page.mouse.move(x, y, steps=random.randint(5, 10))
                        
                        # Tiny pause before clicking
                        await asyncio.sleep(random.uniform(0.1, 0.3))
                        
                        # Click with slight randomization
                        await page.mouse.down()
                        await asyncio.sleep(random.uniform(0.05, 0.15))
                        await page.mouse.up()
                    else:
                        # Fallback to standard click if can't get position
                        await button.click(delay=random.randint(50, 150), force=True)
                except Exception as e:
                    logger.warning(f"Error with precise click, trying force click: {str(e)}")
                    # Last resort - force click
                    try:
                        await button.click(force=True)
                    except Exception as click_error:
                        logger.error(f"Force click failed: {str(click_error)}")
                        # If all else fails, try JavaScript click
                        await page.evaluate("document.querySelector('button:has-text(\"See all\")').click()")
                
                # Wait for the investments to load with patience
                logger.info("Waiting for investments to load...")
                
                # Wait for network activity to settle
                await page.wait_for_load_state("networkidle")
                
                # Extra wait for dynamic content
                await asyncio.sleep(random.uniform(2.0, 3.5))
                
                # Take another screenshot after expansion
                await self.take_screenshot(page, "after_expand")
                
                return True
                
            # Save page HTML for debugging if all methods failed
            html = await page.content()
            with open("data/debug_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info("Saved page HTML to data/debug_page.html for debugging")
            
            logger.info("No 'See all investments' button found")
            return False
                
        except Exception as e:
            logger.error(f"Error expanding investments: {str(e)}")
            await self.take_screenshot(page, "expand_error")
            return False
            
    async def scrape(self, url: str) -> Optional[str]:
        """
        Perform browser automation to scrape a URL with anti-detection measures.
        
        Args:
            url: URL to scrape
            
        Returns:
            HTML content if successful, None otherwise
        """
        playwright = None
        browser = None
        
        try:
            # Set up browser
            playwright, browser, context = await self.setup_browser()
            
            # Create a new page
            page = await context.new_page()
            
            # Apply anti-detection measures if stealth mode is enabled
            if self.stealth_mode:
                await self.bypass_fingerprinting(page)
                await self.apply_stealth_patches(page)
                await self.intercept_bot_checks(page)
            
            # Add a reasonable referer to look legitimate
            referer = random.choice([
                "https://www.google.com/",
                "https://www.linkedin.com/",
                "https://twitter.com/",
                "https://www.crunchbase.com/"
            ])
            
            # Navigate to the URL with referer
            logger.info(f"Navigating to {url}")
            await page.goto(url, referer=referer)
            
            # Wait for the page to load
            await page.wait_for_load_state("networkidle")
            
            # Simulate human-like interaction with the page
            await self.simulate_human_behavior(page)
            
            # Take initial screenshot
            await self.take_screenshot(page, "initial")
            
            # Random delay before proceeding - more natural pattern
            self.random_delay()
            
            # Try to expand investments with human-like behavior
            expanded = await self.expand_investments(page)
            if expanded:
                # Additional wait after expansion
                self.random_delay(1.5)
                
                # More human-like interactions after expansion
                await self.simulate_human_behavior(page)
                
            # Get the final HTML content
            html_content = await page.content()
            
            # Take final screenshot
            await self.take_screenshot(page, "final")
            
            return html_content
            
        except Exception as e:
            logger.error(f"Browser automation error: {str(e)}")
            return None
            
        finally:
            # Cleanup
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
    
    def fetch(self, url: str) -> Optional[str]:
        """
        Synchronous wrapper for the async scrape method.
        
        Args:
            url: URL to scrape
            
        Returns:
            HTML content if successful, None otherwise
        """
        return asyncio.run(self.scrape(url)) 