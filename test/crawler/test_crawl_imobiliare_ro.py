"""Unit tests for Imobiliare.ro crawler"""
import pytest
from bs4 import BeautifulSoup
from flathunter.crawler.imobiliare_ro import ImobiliareRo
from test.utils.config import StringConfig

DUMMY_CONFIG = """
urls:
  - https://www.imobiliare.ro/vanzare-apartamente/bucuresti

notification:
  title: Test
"""
TEST_URL = 'https://www.imobiliare.ro/vanzare-apartamente/bucuresti'

@pytest.fixture
def crawler():
    """Fixture to create an Imobiliare.ro crawler instance"""
    return ImobiliareRo(StringConfig(string=DUMMY_CONFIG))

def test_url_pattern(crawler):
    """Test that Imobiliare.ro URL pattern matches correctly"""
    # Valid URLs
    assert crawler.URL_PATTERN.match("https://www.imobiliare.ro/vanzare-apartamente/bucuresti")
    assert crawler.URL_PATTERN.match("https://www.imobiliare.ro/inchirieri-apartamente/cluj-napoca")
    assert crawler.URL_PATTERN.match("https://www.imobiliare.ro/anunt/12345")
    
    # Invalid URLs
    assert not crawler.URL_PATTERN.match("https://www.storia.ro")
    assert not crawler.URL_PATTERN.match("https://www.immowelt.de")
    assert not crawler.URL_PATTERN.match("https://www.google.com")

def test_crawler_name(crawler):
    """Test that crawler returns correct name"""
    assert crawler.get_name() == "ImobiliareRo"

def test_extract_data_returns_list(crawler):
    """Test that extract_data returns a list even with empty input"""
    # Test with empty soup
    empty_soup = BeautifulSoup("<html><body></body></html>", 'lxml')
    result = crawler.extract_data(empty_soup)
    assert isinstance(result, list)
    assert len(result) == 0

def test_extract_data_with_listing_items(crawler):
    """Test extraction with mock listing items"""
    html = """
    <html>
    <body>
        <div class="listing-item" data-listing-id="12345">
            <h2><a href="/anunt/apartament-3-camere-12345">Apartament 3 camere Bucuresti</a></h2>
            <span class="price">€120,000</span>
            <div class="features">
                3 camere • 75 mp
            </div>
            <span class="location">Bucuresti, Sector 1</span>
            <img src="https://example.com/image1.jpg" alt="Apartament">
        </div>
        <div class="listing-item" data-listing-id="67890">
            <h2><a href="/anunt/apartament-2-camere-67890">Apartament 2 camere Cluj</a></h2>
            <span class="price">€90,000</span>
            <div class="features">
                2 camera • 55 m²
            </div>
            <span class="location">Cluj-Napoca</span>
            <img src="https://example.com/image2.jpg" alt="Apartament">
        </div>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, 'lxml')
    result = crawler.extract_data(soup)
    
    assert isinstance(result, list)
    assert len(result) == 2
    
    # Check first entry
    entry1 = result[0]
    assert entry1['title'] == "Apartament 3 camere Bucuresti"
    assert 'anunt/apartament-3-camere-12345' in entry1['url']
    assert entry1['price'] == "€120,000"
    assert entry1['rooms'] == "3"
    assert entry1['size'] == "75"
    assert entry1['address'] == "Bucuresti, Sector 1"
    assert entry1['image'] == "https://example.com/image1.jpg"
    assert entry1['crawler'] == "ImobiliareRo"
    assert isinstance(entry1['id'], int)
    
    # Check second entry
    entry2 = result[1]
    assert entry2['title'] == "Apartament 2 camere Cluj"
    assert entry2['rooms'] == "2"
    assert entry2['size'] == "55"

def test_extract_data_with_property_items(crawler):
    """Test extraction with alternative class name (property-item)"""
    html = """
    <html>
    <body>
        <div class="property-item">
            <h3><a href="/anunt/casa-4-camere-78901">Casa 4 camere Timisoara</a></h3>
            <div class="pret">250.000 RON</div>
            <ul class="caracteristici">
                <li>4 camere</li>
                <li>120 mp</li>
            </ul>
            <p class="locatie">Timisoara, Timis</p>
            <img data-src="https://example.com/house.jpg" alt="Casa">
        </div>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, 'lxml')
    result = crawler.extract_data(soup)
    
    assert len(result) == 1
    entry = result[0]
    assert entry['title'] == "Casa 4 camere Timisoara"
    assert entry['price'] == "250.000 RON"
    assert entry['rooms'] == "4"
    assert entry['size'] == "120"

def test_extract_data_with_anunt_class(crawler):
    """Test extraction with anunt class (another common pattern)"""
    html = """
    <html>
    <body>
        <div class="anunt" data-id="99999">
            <h2><a href="/anunt/garsoniera-99999">Garsoniera mobilata central</a></h2>
            <span class="price">€45,000</span>
            <div class="features">1 camera • 30 m2</div>
            <span class="address">Bucuresti, Centru</span>
            <img src="https://example.com/garsoniera.jpg">
        </div>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, 'lxml')
    result = crawler.extract_data(soup)
    
    assert len(result) == 1
    entry = result[0]
    assert entry['title'] == "Garsoniera mobilata central"
    assert entry['rooms'] == "1"
    assert entry['size'] == "30"

def test_extract_data_missing_optional_fields(crawler):
    """Test that extraction works even with missing optional fields"""
    html = """
    <html>
    <body>
        <div class="listing-item" data-listing-id="11111">
            <h2><a href="/anunt/teren-11111">Teren intravilan</a></h2>
        </div>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, 'lxml')
    result = crawler.extract_data(soup)
    
    assert len(result) == 1
    entry = result[0]
    assert entry['title'] == "Teren intravilan"
    assert entry['price'] == ""
    assert entry['rooms'] == ""
    assert entry['size'] == ""

def test_extract_data_relative_url(crawler):
    """Test that relative URLs are converted to absolute"""
    html = """
    <html>
    <body>
        <div class="listing-item" data-listing-id="22222">
            <h2><a href="/vanzare/apartament-22222">Apartament de vanzare</a></h2>
            <span class="price">100.000 EUR</span>
        </div>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, 'lxml')
    result = crawler.extract_data(soup)
    
    assert len(result) == 1
    entry = result[0]
    assert entry['url'].startswith("https://www.imobiliare.ro")
    assert "apartament-22222" in entry['url']

def test_extract_data_id_from_url(crawler):
    """Test ID extraction when data-listing-id is not present"""
    html = """
    <html>
    <body>
        <div class="listing-item">
            <h2><a href="/anunt/apartament/54321">Apartament nou</a></h2>
            <span class="price">€85,000</span>
        </div>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, 'lxml')
    result = crawler.extract_data(soup)
    
    assert len(result) == 1
    entry = result[0]
    # ID should be extracted from URL
    assert isinstance(entry['id'], int)
    assert entry['id'] > 0

def test_extract_data_skips_invalid_entries(crawler):
    """Test that invalid entries are skipped"""
    html = """
    <html>
    <body>
        <div class="listing-item" data-listing-id="33333">
            <!-- No title, should be skipped -->
            <span class="price">€100,000</span>
        </div>
        <div class="listing-item" data-listing-id="44444">
            <h2>Valid entry</h2>
            <a href="/anunt/valid-44444">Link</a>
            <span class="price">€200,000</span>
        </div>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, 'lxml')
    result = crawler.extract_data(soup)
    
    # Only the valid entry should be extracted
    assert len(result) == 1
    assert "Valid entry" in result[0]['title']

@pytest.mark.skipif(True, reason="Requires live website access and Chrome driver - use for manual testing only")
def test_process_expose_fetches_details(crawler):
    """Integration test - fetches real data from Imobiliare.ro"""
    soup = crawler.get_page(TEST_URL)
    assert soup is not None
    entries = crawler.extract_data(soup)
    assert entries is not None
    assert len(entries) > 0
    updated_entries = [crawler.get_expose_details(expose) for expose in entries]
    for expose in updated_entries:
        print(expose)
        for attr in ['title', 'price', 'url']:
            assert expose[attr] is not None
