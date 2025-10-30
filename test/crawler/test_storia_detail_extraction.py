"""Unit tests for Storia detail extraction"""
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

DETAIL_PAGE_HTML = """
<html>
<body>
    <div data-cy="ad.description">
        <p>Apartament modern cu 3 camere in zona centrala. 
        Bloc nou, finisaje premium, vedere superba.</p>
    </div>
    
    <div data-cy="ad.top-information">
        <div class="css-details">
            <dt>Anul construcției</dt>
            <dd>2020</dd>
        </div>
        <div class="css-details">
            <dt>Etaj</dt>
            <dd>4</dd>
        </div>
        <div class="css-details">
            <dt>Tip construcție</dt>
            <dd>Cărămidă</dd>
        </div>
        <div class="css-details">
            <dt>Stare</dt>
            <dd>Nou</dd>
        </div>
        <div class="css-details">
            <dt>Încălzire</dt>
            <dd>Centrala termică</dd>
        </div>
        <div class="css-details">
            <dt>Parcare</dt>
            <dd>Subsol</dd>
        </div>
    </div>
    
    <div data-cy="ad.gallery">
        <picture>
            <img src="https://example.com/image1.jpg" alt="Photo 1">
        </picture>
        <picture>
            <img src="https://example.com/image2.jpg" alt="Photo 2">
        </picture>
        <picture>
            <img src="https://example.com/image3.jpg" alt="Photo 3">
        </picture>
    </div>
</body>
</html>
"""


@pytest.fixture
def crawler():
    """Fixture to create a Storia crawler instance"""
    return Storia(StringConfig(string=DUMMY_CONFIG))


def test_extract_description(crawler):
    """Test description extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'description' in result
    assert 'Apartament modern' in result['description']
    assert 'zona centrala' in result['description']


def test_extract_construction_year(crawler):
    """Test construction year extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'construction_year' in result
    assert result['construction_year'] == '2020'


def test_extract_floor(crawler):
    """Test floor extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'floor' in result
    assert result['floor'] == '4'


def test_extract_building_type(crawler):
    """Test building type extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'building_type' in result
    assert result['building_type'] == 'Cărămidă'


def test_extract_condition(crawler):
    """Test condition extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'condition' in result
    assert result['condition'] == 'Nou'


def test_extract_heating(crawler):
    """Test heating extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'heating' in result
    assert result['heating'] == 'Centrala termică'


def test_extract_parking(crawler):
    """Test parking extraction"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'parking' in result
    assert result['parking'] == 'Subsol'


def test_extract_all_images(crawler):
    """Test extraction of all images"""
    soup = BeautifulSoup(DETAIL_PAGE_HTML, 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    assert 'images' in result
    assert len(result['images']) == 3
    assert 'image1.jpg' in result['images'][0]
    assert 'image2.jpg' in result['images'][1]
    assert 'image3.jpg' in result['images'][2]


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


def test_extract_with_empty_soup(crawler):
    """Test with empty HTML"""
    soup = BeautifulSoup("<html><body></body></html>", 'lxml')
    expose = {'id': 1, 'title': 'Test'}
    
    result = crawler._populate_detail_from_soup(expose, soup)
    
    # Should have at least 'from' field set
    assert 'from' in result
    # Other fields may not exist
