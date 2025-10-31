"""Quick test script to check Imobiliare.ro page loading"""
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flathunter.crawler.imobiliare_ro import ImobiliareRo
from flathunter.logging import logger

# Test configuration - use StringConfig from test utils
from test.utils.config import StringConfig

yaml_config = """
urls:
  - https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000
"""

if __name__ == "__main__":
    logger.info("Testing Imobiliare.ro page loading...")

    config = StringConfig(string=yaml_config)
    crawler = ImobiliareRo(config)

    test_url = "https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000"
    logger.info(f"Fetching page: {test_url}")

    try:
        soup = crawler.get_page(test_url)
        page_html = str(soup)

        print(f"\n{'='*60}")
        print(f"Page length: {len(page_html)} characters")
        print(f"{'='*60}")

        if len(page_html) < 1000:
            print("\n❌ ERROR: Page is too short (possible bot detection)")
            print(f"\nPage preview:\n{page_html[:500]}")
        else:
            print("\n✅ SUCCESS: Page loaded with content")

            # Check for expected Imobiliare.ro elements
            if 'imobiliare.ro' in page_html.lower():
                print("✅ Contains 'imobiliare.ro' in HTML")
            if 'listing-item' in page_html or 'anunt' in page_html:
                print("✅ Contains listing elements")

            # Count listings
            listings = soup.find_all('div', class_=re.compile(r'listing-item|anunt'))
            print(f"\n📊 Found {len(listings)} potential listing elements")

            # Try to extract data
            listings = crawler.extract_data(soup)
            print(f"📊 Extracted {len(listings)} listings")

            if listings:
                print(f"\n📝 First listing sample:")
                first = listings[0]
                print(f"   Title: {first.get('title', 'N/A')[:60]}...")
                print(f"   Price: {first.get('price', 'N/A')}")
                print(f"   Rooms: {first.get('rooms', 'N/A')}")
                print(f"   Size: {first.get('size', 'N/A')}")
                print(f"   URL: {first.get('url', 'N/A')[:60]}...")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Close the driver properly
        try:
            crawler.close_driver()
            logger.info("WebDriver closed")
        except:
            pass