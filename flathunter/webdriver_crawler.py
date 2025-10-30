"""Expose crawler for Kleinanzeigen"""
from typing import Optional
import re

from selenium.webdriver import Chrome
from bs4 import BeautifulSoup

from flathunter.abstract_crawler import Crawler
from flathunter.chrome_wrapper import get_chrome_driver
from flathunter.exceptions import DriverLoadException
from flathunter.logging import logger

class WebdriverCrawler(Crawler):
    """Parent class of crawlers that use webdriver rather than `requests` to fetch pages"""

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.driver = None

    def get_driver(self) -> Optional[Chrome]:
        """Lazy method to fetch the driver as required at runtime"""
        if self.driver is not None:
            return self.driver
        driver_arguments = self.config.captcha_driver_arguments()
        self.driver = get_chrome_driver(driver_arguments)
        return self.driver

    def get_driver_force(self) -> Chrome:
        """Fetch the driver, and throw an exception if it is not configured or available"""
        res = self.get_driver()
        if res is None:
            raise DriverLoadException("Unable to load chrome driver when expected")
        return res

    def get_page(self, search_url, driver=None, page_no=None) -> BeautifulSoup:
        """Applies a page number to a formatted search URL and fetches the exposes at that page"""
        return self.get_soup_from_url(search_url, driver=self.get_driver())

    def _clean_image_url(self, url):
        """Clean and validate image URL"""
        if not url:
            return None
        
        # Remove whitespace
        url = str(url).strip()
        
        # Skip data URLs, placeholders, and invalid URLs
        if not url or url.startswith('data:') or 'placeholder' in url.lower():
            return None
        
        # Handle protocol-relative URLs
        if url.startswith('//'):
            url = 'https:' + url
        
        return url

    def _populate_detail_from_soup(self, expose, soup):
        """Extract additional details from listing detail page. To be overridden by subclasses."""
        return expose

    def get_expose_details(self, expose):
        """Loads additional details for an expose by fetching the detail page"""
        try:
            soup = self.get_page(expose['url'], self.get_driver())
            return self._populate_detail_from_soup(expose, soup)
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Error fetching details for expose %s: %s", expose.get('url', 'unknown'), str(e))
            return expose
