"""Test WebDriver cleanup fix"""
import sys
import os

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
    logger.info("Testing WebDriver cleanup...")

    config = StringConfig(string=yaml_config)
    crawler = ImobiliareRo(config)

    try:
        # Get driver
        driver = crawler.get_driver()
        if driver:
            print("✅ WebDriver created successfully")
            # Test basic functionality
            driver.get("about:blank")
            print("✅ WebDriver navigation works")
        else:
            print("❌ Failed to create WebDriver")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Test the new cleanup method
        print("🧹 Testing WebDriver cleanup...")
        try:
            crawler.close_driver()
            print("✅ WebDriver closed cleanly")
        except Exception as e:
            print(f"❌ Cleanup error: {str(e)}")

    print("🎉 Test completed - no handle errors should appear above")