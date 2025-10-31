#!/usr/bin/env python3
"""Quick test for Imobiliare.ro crawler with new selectors"""

import os
import sys
import time

# Set up environment
os.environ['FLATHUNTER_TARGET_URLS'] = 'https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000'

from flathunter.crawler.imobiliare_ro import ImobiliareRo
from flathunter.config import Config

def test_crawler():
    print("🧪 Testing Imobiliare.ro crawler with updated selectors...")

    try:
        # Create config and crawler
        config = Config()
        crawler = ImobiliareRo(config)

        # Test page loading with shorter timeout
        print("📄 Loading page...")
        soup = crawler.get_page('https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000')

        if soup and len(str(soup)) > 1000:
            print("✅ Page loaded successfully")

            # Test data extraction
            print("🔍 Extracting data...")
            entries = crawler.extract_data(soup)

            print(f"📊 Found {len(entries)} entries")

            if entries:
                print("🎯 First entry sample:")
                entry = entries[0]
                for key in ['title', 'price', 'rooms', 'size', 'address']:
                    value = entry.get(key, 'N/A')
                    print(f"   {key}: {str(value)[:60]}{'...' if len(str(value)) > 60 else ''}")
                print("✅ Data extraction working!")
            else:
                print("❌ No entries found - selectors may need adjustment")
        else:
            print("❌ Page loading failed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    finally:
        try:
            crawler.close_driver()
            print("🧹 WebDriver closed cleanly")
        except:
            pass

    return True

if __name__ == "__main__":
    success = test_crawler()
    sys.exit(0 if success else 1)