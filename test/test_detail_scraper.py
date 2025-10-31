"""Unit tests for Detail Scraper"""
import pytest
import datetime
from unittest.mock import Mock, MagicMock, patch
from bs4 import BeautifulSoup

from detail_scraper import DetailScraper
from test.utils.config import StringConfig

DUMMY_CONFIG = """
urls:
  - https://www.storia.ro/ro/rezultate/vanzare/apartament/cluj/cluj--napoca

loop:
  active: yes
  sleeping_time: 10
  random_jitter: False

detail_scraper:
  loop_active: no
  hours_lookback: 24

notification:
  title: Test
"""


@pytest.fixture
def config():
    """Fixture to create a config instance"""
    return StringConfig(string=DUMMY_CONFIG)


@pytest.fixture
def mock_id_watch():
    """Fixture to create a mock IdMaintainer"""
    mock = Mock()
    mock.get_exposes_since = Mock(return_value=[])
    mock.save_expose = Mock()
    return mock


@pytest.fixture
def scraper(config, mock_id_watch):
    """Fixture to create a DetailScraper instance"""
    return DetailScraper(config, mock_id_watch)


def test_detail_scraper_initialization(scraper):
    """Test that DetailScraper initializes correctly"""
    assert scraper.config is not None
    assert scraper.id_watch is not None
    assert 'Storia' in scraper.crawlers
    assert 'ImobiliareRo' in scraper.crawlers


def test_get_listings_to_update_filters_correctly(scraper, mock_id_watch):
    """Test that get_listings_to_update filters for Storia and ImobiliareRo only"""
    mock_exposes = [
        {'id': 1, 'crawler': 'Storia', 'title': 'Test 1'},
        {'id': 2, 'crawler': 'ImobiliareRo', 'title': 'Test 2'},
        {'id': 3, 'crawler': 'Immobilienscout', 'title': 'Test 3'},  # Should be filtered out
        {'id': 4, 'crawler': 'Storia', 'title': 'Test 4'},
    ]
    mock_id_watch.get_exposes_since.return_value = mock_exposes
    
    result = scraper.get_listings_to_update(hours_ago=24)
    
    assert len(result) == 3
    assert all(e['crawler'] in ['Storia', 'ImobiliareRo'] for e in result)
    assert mock_id_watch.get_exposes_since.called


def test_update_listing_details_storia(scraper, mock_id_watch):
    """Test updating details for a Storia listing"""
    expose = {
        'id': 1,
        'crawler': 'Storia',
        'url': 'https://www.storia.ro/ro/oferta/test',
        'title': 'Test Listing'
    }
    
    # Mock the crawler's get_expose_details method
    with patch.object(scraper.storia_crawler, 'get_expose_details') as mock_get_details:
        mock_get_details.return_value = {
            **expose,
            'description': 'Full description',
            'images': ['img1.jpg', 'img2.jpg'],
            'construction_year': '2020'
        }
        
        result = scraper.update_listing_details(expose)
        
        assert result is True
        assert mock_get_details.called
        assert mock_id_watch.save_expose.called


def test_update_listing_details_imobiliare_ro(scraper, mock_id_watch):
    """Test updating details for an ImobiliareRo listing"""
    expose = {
        'id': 2,
        'crawler': 'ImobiliareRo',
        'url': 'https://www.imobiliare.ro/anunt/test',
        'title': 'Test Listing'
    }
    
    with patch.object(scraper.imobiliare_crawler, 'get_expose_details') as mock_get_details:
        mock_get_details.return_value = {
            **expose,
            'description': 'Full description',
            'floor': '3'
        }
        
        result = scraper.update_listing_details(expose)
        
        assert result is True
        assert mock_get_details.called
        assert mock_id_watch.save_expose.called


def test_update_listing_details_skips_other_crawlers(scraper, mock_id_watch):
    """Test that non-Storia/ImobiliareRo listings are skipped"""
    expose = {
        'id': 3,
        'crawler': 'Immobilienscout',
        'url': 'https://www.immobilienscout24.de/test',
        'title': 'Test Listing'
    }
    
    result = scraper.update_listing_details(expose)
    
    assert result is False
    assert not mock_id_watch.save_expose.called


def test_update_listing_details_no_new_data(scraper, mock_id_watch):
    """Test that listing without new data returns False"""
    expose = {
        'id': 1,
        'crawler': 'Storia',
        'url': 'https://www.storia.ro/ro/oferta/test',
        'title': 'Test Listing',
        'description': 'Existing description'
    }
    
    with patch.object(scraper.storia_crawler, 'get_expose_details') as mock_get_details:
        # Return same data, no new fields
        mock_get_details.return_value = expose.copy()
        
        result = scraper.update_listing_details(expose)
        
        assert result is False


def test_update_listing_details_handles_errors(scraper, mock_id_watch):
    """Test that errors are handled gracefully"""
    expose = {
        'id': 1,
        'crawler': 'Storia',
        'url': 'https://www.storia.ro/ro/oferta/test',
        'title': 'Test Listing'
    }
    
    with patch.object(scraper.storia_crawler, 'get_expose_details') as mock_get_details:
        mock_get_details.side_effect = Exception("Network error")
        
        result = scraper.update_listing_details(expose)
        
        assert result is False
        assert not mock_id_watch.save_expose.called


def test_scrape_details_empty_list(scraper, mock_id_watch):
    """Test scrape_details with no listings"""
    mock_id_watch.get_exposes_since.return_value = []
    
    # Should not raise any errors
    scraper.scrape_details(hours_ago=24)
    
    assert mock_id_watch.get_exposes_since.called
    assert not mock_id_watch.save_expose.called


def test_scrape_details_with_listings(scraper, mock_id_watch):
    """Test scrape_details with multiple listings"""
    mock_exposes = [
        {'id': 1, 'crawler': 'Storia', 'url': 'https://storia.ro/1', 'title': 'Test 1'},
        {'id': 2, 'crawler': 'ImobiliareRo', 'url': 'https://imobiliare.ro/2', 'title': 'Test 2'},
    ]
    mock_id_watch.get_exposes_since.return_value = mock_exposes
    
    with patch.object(scraper, 'update_listing_details') as mock_update:
        mock_update.return_value = True
        
        # Mock time.sleep to avoid delays in tests
        with patch('detail_scraper.time.sleep'):
            scraper.scrape_details(hours_ago=24)
        
        assert mock_update.call_count == 2
