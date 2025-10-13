"""Unit tests for Storia.ro crawler"""
import pytest
from bs4 import BeautifulSoup
from flathunter.crawler.storia import Storia
from test.utils.config import StringConfig

DUMMY_CONFIG = """
urls:
  - https://www.storia.ro/ro/rezultate/vanzare/apartament/cluj/cluj--napoca

notification:
  title: Test
"""
TEST_URL = 'https://www.storia.ro/ro/rezultate/vanzare/apartament/cluj/cluj--napoca'

@pytest.fixture
def crawler():
    """Fixture to create a Storia crawler instance"""
    return Storia(StringConfig(string=DUMMY_CONFIG))

def test_url_pattern(crawler):
    """Test that Storia URL pattern matches correctly"""
    # Valid URLs
    assert crawler.URL_PATTERN.match("https://www.storia.ro/ro/rezultate/vanzare/apartament/cluj/cluj--napoca")
    assert crawler.URL_PATTERN.match("https://www.storia.ro/ro/oferta/ID123ABC")
    
    # Invalid URLs
    assert not crawler.URL_PATTERN.match("https://www.immowelt.de")
    assert not crawler.URL_PATTERN.match("https://www.google.com")

def test_crawler_name(crawler):
    """Test that crawler returns correct name"""
    assert crawler.get_name() == "Storia"

def test_extract_data_returns_list(crawler):
    """Test that extract_data returns a list even with empty input"""
    # Test with empty soup
    empty_soup = BeautifulSoup("<html><body></body></html>", 'lxml')
    result = crawler.extract_data(empty_soup)
    assert isinstance(result, list)
    assert len(result) == 0

@pytest.mark.skipif(True, reason="Requires live website access and Chrome driver - use for manual testing only")
def test_process_expose_fetches_details(crawler):
    """Integration test - fetches real data from Storia.ro"""
    soup = crawler.get_page(TEST_URL)
    assert soup is not None
    entries = crawler.extract_data(soup)
    assert entries is not None
    assert len(entries) > 0
    updated_entries = [crawler.get_expose_details(expose) for expose in entries]
    for expose in updated_entries:
        print(expose)
        for attr in ['title', 'price', 'size', 'rooms', 'address', 'from']:
            assert expose[attr] is not None