"""Test to save Imobiliare.ro HTML for inspection"""
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flathunter.crawler.imobiliare_ro import ImobiliareRo
from flathunter.logging import logger
from test.utils.config import StringConfig
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

yaml_config = """
urls:
  - https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000
"""

if __name__ == "__main__":
    logger.info("Saving Imobiliare.ro HTML for inspection...")
    
    config = StringConfig(string=yaml_config)
    crawler = ImobiliareRo(config)
    driver = None  # Initialize to avoid unbound variable error
    
    test_url = "https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000"
    logger.info(f"Fetching page: {test_url}")

    try:
        driver = crawler.get_driver()
        if driver is None:
            print("❌ Could not get WebDriver")
            sys.exit(1)
            
        driver.get(test_url)

        # Wait a bit for page to load
        time.sleep(5)

        # Save the HTML
        page_source = driver.page_source

        with open('imobiliare_sample.html', 'w', encoding='utf-8') as f:
            f.write(page_source)

        print(f"\n✅ Saved HTML to imobiliare_sample.html")
        print(f"Page length: {len(page_source)} characters")

        # Check for common elements
        if 'imobiliare.ro' in page_source.lower():
            print("✅ Contains 'imobiliare.ro'")
        if 'apartament' in page_source.lower():
            print("✅ Contains 'apartament'")
        if 'anunt' in page_source.lower():
            print("✅ Contains 'anunt'")

        # Try to find any divs that might be listings
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, 'lxml')

        # Look for various patterns
        potential_listings = []
        potential_listings.extend(soup.find_all('article'))
        potential_listings.extend(soup.find_all('div', class_=re.compile(r'card|item|listing')))
        potential_listings.extend(soup.find_all('div', attrs={'data-id': True}))
        potential_listings.extend(soup.find_all('div', attrs={'data-listing-id': True}))

        print(f"\n📊 Found {len(set(potential_listings))} potential listing elements")

        # Show first few potential listings
        for i, listing in enumerate(list(potential_listings[:3])):
            print(f"\nListing {i+1}:")
            print(f"  Tag: {listing.name}")
            print(f"  Classes: {listing.get('class', [])}")
            print(f"  Data attrs: {[k for k in listing.attrs.keys() if k.startswith('data-')]}")
            print(f"  First 200 chars: {str(listing)[:200]}...")

    finally:
        try:
            if 'driver' in locals() and driver is not None:
                driver.quit()
            logger.info("WebDriver closed")
        except Exception as e:
            # Ignore cleanup errors - browser might already be closed
            logger.debug(f"WebDriver cleanup error (expected): {e}")
            pass