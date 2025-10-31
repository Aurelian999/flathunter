"""Unit tests for ImobiliareRo detail extraction"""
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

DETAIL_PAGE_HTML = """
<html>
<body>
    <div class="description-container">
        <p>Apartament deosebit cu 2 camere in Bucuresti. 
        Renovat complet, mobilat si utilat modern.</p>
    </div>
    
    <div class="caracteristici-details">
        <ul>
            <li>An construcție: 2018</li>
            <li>Etaj: 3 din 5</li>
            <li>Tip construcție: Beton armat</li>
            <li>Stare imobil: Renovat</li>
            <li>Sistem încălzire: Centrala proprie</li>
            <li>Parcare disponibila in curte</li>
        </ul>
    </div>
    
    <div class="gallery-section">
        <picture>
            <img src="https://example.ro/photo1.jpg" alt="Imagine 1">
        </picture>
        <picture>
            <img data-src="https://example.ro/photo2.jpg" alt="Imagine 2">
        </picture>
        <img data-lazy-src="https://example.ro/photo3.jpg" alt="Imagine 3">
    </div>
</body>
</html>
"""


@pytest.fixture
def crawler():
    """Fixture to create an ImobiliareRo crawler instance"""
    return ImobiliareRo(StringConfig(string=DUMMY_CONFIG))


def test_extract_description(crawler):
    """Test description extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'description' in result
    assert 'Apartament deosebit' in result['description']
    assert 'mobilat si utilat' in result['description']


def test_extract_construction_year(crawler):
    """Test construction year extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'construction_year' in result
    assert result['construction_year'] == '2018'


def test_extract_floor(crawler):
    """Test floor extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'floor' in result
    # Should extract "3" or "3 din 5"
    assert '3' in result['floor']


def test_extract_building_type(crawler):
    """Test building type extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'building_type' in result
    assert 'Beton' in result['building_type'] or 'armat' in result['building_type']


def test_extract_condition(crawler):
    """Test condition extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'condition' in result
    assert 'Renovat' in result['condition']


def test_extract_heating(crawler):
    """Test heating extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'heating' in result
    assert 'Centrala' in result['heating']


def test_extract_parking(crawler):
    """Test parking extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'parking' in result
    assert 'parcare' in result['parking'].lower()


def test_extract_all_images(crawler):
    """Test extraction of all images from various attributes"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'images' in result
    assert len(result['images']) == 3
    assert any('photo1.jpg' in img for img in result['images'])
    assert any('photo2.jpg' in img for img in result['images'])
    assert any('photo3.jpg' in img for img in result['images'])


def test_extract_sets_main_image(crawler):
    """Test that first image becomes main image if not set"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'image' in result
    assert result['image'] == result['images'][0]


def test_extract_with_none_soup(crawler):
    """Test handling of None soup"""
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, None)
    
    # Should return expose unchanged
    assert result == expose


def test_extract_with_missing_fields(crawler):
    """Test with HTML missing some fields"""
    minimal_html = """
    <html>
    <body>
        <div class="description-container">
            <p>Minimal description</p>
        </div>
    </body>
    </html>
    """
    soup = BeautifulSoup(minimal_html, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    # Should have at least description and from
    assert 'description' in result
    assert 'from' in result
    # Other fields may not exist, which is fine
