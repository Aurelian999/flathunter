"""Simple test to check if Imobiliare.ro page loads without timeout"""
import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flathunter.crawler.imobiliare_ro import ImobiliareRo
from flathunter.logging import logger
from test.utils.config import StringConfig

yaml_config = """
urls:
  - https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000
"""

if __name__ == "__main__":
    logger.info("Testing Imobiliare.ro page loading (simple)...")

    config = StringConfig(string=yaml_config)
    crawler = ImobiliareRo(config)

    test_url = "https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000"
    logger.info(f"Fetching page: {test_url}")

    start_time = time.time()

    try:
        soup = crawler.get_page(test_url)
        page_html = str(soup)

        elapsed = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"Page loaded in {elapsed:.1f} seconds")
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
            if 'anunt' in page_html or 'apartament' in page_html:
                print("✅ Contains Romanian real estate terms")

            # Check for listing indicators
            if 'listing-item' in page_html or 'data-listing-id' in page_html:
                print("✅ Contains listing elements")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR after {elapsed:.1f} seconds: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Close the driver properly
        try:
            crawler.close_driver()
            logger.info("WebDriver closed")
        except:
            pass