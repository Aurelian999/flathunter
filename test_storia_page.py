"""Quick test script to check Storia.ro page loading"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flathunter.crawler.storia import Storia
from flathunter.logging import logger

# Test configuration - use StringConfig from test utils
from test.utils.config import StringConfig

yaml_config = """
urls:
  - https://www.storia.ro/ro/rezultate/inchiriere/apartament/bucuresti
"""

if __name__ == "__main__":
    logger.info("Testing Storia.ro page loading...")
    
    config = StringConfig(string=yaml_config)
    crawler = Storia(config)
    
    test_url = "https://www.storia.ro/ro/rezultate/inchiriere/apartament/bucuresti"
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
            
            # Check for expected Storia.ro elements
            if 'storia.ro' in page_html.lower():
                print("✅ Contains 'storia.ro' in HTML")
            if 'listing-item' in page_html:
                print("✅ Contains 'listing-item' elements")
            if 'article' in page_html:
                print("✅ Contains article tags")
            
            # Count listings
            articles = soup.find_all('article')
            print(f"\n📊 Found {len(articles)} article elements")
            
            # Debug first article structure
            if articles:
                print(f"\n🔍 First article structure:")
                first_article = articles[0]
                print(f"   Classes: {first_article.get('class', [])}")
                print(f"   Data attributes: {[k for k in first_article.attrs.keys() if k.startswith('data-')]}")
                
                # Save full HTML to file for inspection
                with open('storia_sample.html', 'w', encoding='utf-8') as f:
                    f.write(str(first_article.prettify()))
                print(f"   ✅ Saved first article HTML to storia_sample.html")
            
            # Try to extract data
            listings = crawler.extract_data(soup)
            print(f"\n📊 Extracted {len(listings)} listings")
            
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
        # Close the driver
        try:
            driver = crawler.get_driver()
            if driver:
                driver.quit()
                logger.info("WebDriver closed")
        except:
            pass
