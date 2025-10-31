"""Unit tests for WebdriverCrawler enhancements"""
import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from flathunter.webdriver_crawler import WebdriverCrawler
from test.utils.config import StringConfig

DUMMY_CONFIG = """
urls:
  - https://www.example.com

notification:
  title: Test
"""


@pytest.fixture
def config():
    """Fixture to create a config instance"""
    return StringConfig(string=DUMMY_CONFIG)


@pytest.fixture
def crawler(config):
    """Fixture to create a WebdriverCrawler instance"""
    return WebdriverCrawler(config)


class TestCleanImageUrl:
    """Tests for _clean_image_url method"""
    
    def test_clean_image_url_valid_http(self, crawler):
        """Test with valid HTTP URL"""
        url = "http://example.com/image.jpg"
        result = crawler._clean_image_url(url)
        assert result == url
    
    def test_clean_image_url_valid_https(self, crawler):
        """Test with valid HTTPS URL"""
        url = "https://example.com/image.jpg"
        result = crawler._clean_image_url(url)
        assert result == url
    
    def test_clean_image_url_protocol_relative(self, crawler):
        """Test with protocol-relative URL"""
        url = "//example.com/image.jpg"
        result = crawler._clean_image_url(url)
        assert result == "https://example.com/image.jpg"
    
    def test_clean_image_url_with_whitespace(self, crawler):
        """Test URL with whitespace"""
        url = "  https://example.com/image.jpg  "
        result = crawler._clean_image_url(url)
        assert result == "https://example.com/image.jpg"
    
    def test_clean_image_url_data_uri(self, crawler):
        """Test that data URIs are rejected"""
        url = "data:image/png;base64,iVBORw0KGgoAAAANS..."
        result = crawler._clean_image_url(url)
        assert result is None
    
    def test_clean_image_url_placeholder(self, crawler):
        """Test that placeholder URLs are rejected"""
        url = "https://example.com/placeholder.jpg"
        result = crawler._clean_image_url(url)
        assert result is None
    
    def test_clean_image_url_none(self, crawler):
        """Test with None input"""
        result = crawler._clean_image_url(None)
        assert result is None
    
    def test_clean_image_url_empty_string(self, crawler):
        """Test with empty string"""
        result = crawler._clean_image_url("")
        assert result is None


class TestPopulateDetailFromSoup:
    """Tests for _populate_detail_from_soup method"""
    
    def test_populate_detail_from_soup_base_implementation(self, crawler):
        """Test base implementation returns expose unchanged"""
        expose = {'id': 1, 'title': 'Test'}
        soup = BeautifulSoup("<html><body>Test</body></html>", 'lxml')
        
        result = crawler._populate_detail_from_soup(expose, soup)
        
        assert result == expose


class TestGetExposeDetails:
    """Tests for get_expose_details method"""
    
    def test_get_expose_details_success(self, crawler):
        """Test successful detail fetching"""
        expose = {'id': 1, 'url': 'https://example.com/listing', 'title': 'Test'}
        soup = BeautifulSoup("<html><body>Test</body></html>", 'lxml')
        
        with patch.object(crawler, 'get_page', return_value=soup):
            with patch.object(crawler, 'get_driver', return_value=Mock()):
                with patch.object(crawler, '_populate_detail_from_soup') as mock_populate:
                    mock_populate.return_value = {**expose, 'description': 'Added detail'}
                    
                    result = crawler.get_expose_details(expose)
                    
                    assert mock_populate.called
                    assert 'description' in result
    
    def test_get_expose_details_error_handling(self, crawler):
        """Test that errors are caught and original expose returned"""
        expose = {'id': 1, 'url': 'https://example.com/listing', 'title': 'Test'}
        
        with patch.object(crawler, 'get_page', side_effect=Exception("Network error")):
            with patch.object(crawler, 'get_driver', return_value=Mock()):
                result = crawler.get_expose_details(expose)
                
                # Should return original expose on error
                assert result == expose
