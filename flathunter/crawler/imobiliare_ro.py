"""Expose crawler for Imobiliare.ro (Romanian real estate site)"""
import re
import datetime
import hashlib

from bs4 import BeautifulSoup, Tag

from flathunter.logging import logger
from flathunter.webdriver_crawler import WebdriverCrawler


class ImobiliareRo(WebdriverCrawler):
    """Implementation of Crawler interface for Imobiliare.ro"""

    URL_PATTERN = re.compile(r'https://www\.imobiliare\.ro')

    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def get_page(self, search_url, driver=None, page_no=None):
        """Applies a page number to a formatted search URL and fetches the exposes at that page
        Imobiliare.ro uses JavaScript rendering, so we always use the webdriver"""
        import time
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        driver = self.get_driver()
        if driver is None:
            logger.error("WebDriver not available for Imobiliare.ro - Chrome is required")
            return BeautifulSoup("<html><body></body></html>", 'lxml')
        
        try:
            # Load the page
            driver.get(search_url)
            
            # Wait for Imobiliare.ro specific content to load
            # Try multiple selectors to ensure the page has loaded
            try:
                # Wait for listing items to appear
                WebDriverWait(driver, 15).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, '.listing-item') or
                              d.find_elements(By.CSS_SELECTOR, '[data-listing-id]') or
                              d.find_elements(By.CSS_SELECTOR, '.property-item') or
                              d.find_elements(By.CLASS_NAME, 'anunt')
                )
                logger.debug("Imobiliare.ro: Content loaded successfully")
            except Exception as wait_error:
                logger.warning("Imobiliare.ro: Timeout waiting for listings, trying anyway: %s", str(wait_error))
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Scroll to trigger lazy loading (Imobiliare.ro may use lazy loading)
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            except Exception as scroll_error:
                logger.debug("Could not scroll page: %s", str(scroll_error))
            
            # Get the page source after JavaScript execution
            page_source = driver.page_source
            
            # Debug: Check if we got actual content
            if len(page_source) < 1000:
                logger.warning("Imobiliare.ro returned very short page (%d chars) - possible bot detection", len(page_source))
                logger.debug("Page source preview: %s", page_source[:500])
            else:
                logger.debug("Imobiliare.ro: Retrieved page with %d characters", len(page_source))
            
            return BeautifulSoup(page_source, 'lxml')
            
        except Exception as e:
            logger.error("Error loading Imobiliare.ro page: %s", str(e))
            return BeautifulSoup("<html><body></body></html>", 'lxml')

    def _populate_detail_from_soup(self, expose, soup):
        """Extract additional details from Imobiliare.ro listing page"""
        expose = super()._populate_detail_from_soup(expose, soup)

        if soup is None:
            return expose

        # Set default availability date
        date = datetime.datetime.now().strftime("%d.%m.%Y")
        expose['from'] = date

        # Try to find availability date
        # Imobiliare.ro might have it in different places depending on listing type
        details_section = soup.find("div", class_=re.compile(r".*details.*|.*detalii.*", re.IGNORECASE))
        if isinstance(details_section, Tag):
            text = details_section.get_text(strip=True).lower()
            if 'disponibil' in text or 'disponibilitate' in text:
                # Extract date if present
                date_match = re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', text)
                if date_match:
                    expose['from'] = date_match.group(0)

        # Extract description
        description_container = soup.find("div", class_=re.compile(r".*description.*|.*descriere.*", re.IGNORECASE))
        if not description_container:
            # Alternative locations
            description_container = soup.find("div", attrs={"id": re.compile(r".*description.*", re.IGNORECASE)})
        
        if isinstance(description_container, Tag):
            text = description_container.get_text("\n", strip=True)
            if text:
                expose['description'] = text

        # Extract images from gallery
        gallery = soup.find("div", class_=re.compile(r".*gallery.*|.*galerie.*", re.IGNORECASE))
        if not gallery:
            # Alternative location
            gallery = soup.find("div", attrs={"id": re.compile(r".*gallery.*", re.IGNORECASE)})
        
        if isinstance(gallery, Tag):
            images = expose.get('images', [])
            
            # Check for picture elements
            for picture in gallery.find_all('picture'):
                img = picture.find('img')
                if isinstance(img, Tag):
                    # Try multiple attributes where image URL might be
                    for attr in ['src', 'data-src', 'data-lazy-src', 'srcset']:
                        url = img.get(attr)
                        if url:
                            # Handle srcset format
                            if attr == 'srcset':
                                url = url.split(',')[0].split(' ')[0]
                            clean_url = self._clean_image_url(url)
                            if clean_url and clean_url not in images:
                                images.append(clean_url)
                                break
            
            # Also check for direct img tags
            for img in gallery.find_all('img'):
                if isinstance(img, Tag):
                    for attr in ['src', 'data-src', 'data-original', 'data-lazy-src']:
                        url = self._clean_image_url(img.get(attr))
                        if url and url not in images:
                            images.append(url)
                            break
            
            if images:
                expose['images'] = images
                if not expose.get('image') or 'placeholder' in str(expose.get('image')):
                    expose['image'] = images[0]

        return expose

    # pylint: disable=too-many-locals
    def extract_data(self, raw_data: BeautifulSoup):
        """Extracts all exposes from Imobiliare.ro search results page"""
        entries = []
        soup_res = raw_data
        
        if not isinstance(soup_res, BeautifulSoup):
            logger.warning("Invalid soup object provided to Imobiliare.ro crawler")
            return []

        # Imobiliare.ro typically uses various class names for listings
        # Try multiple selectors to find listing items
        advertisements = []
        
        # Try common patterns for Romanian real estate sites
        for selector in [
            {'class': re.compile(r'listing-item')},
            {'class': re.compile(r'property-item')},
            {'class': 'anunt'},
            {'attrs': {'data-listing-id': True}},
            {'class': re.compile(r'.*card.*item.*', re.IGNORECASE)},
        ]:
            if 'attrs' in selector:
                advertisements = soup_res.find_all('div', attrs=selector['attrs'])
            else:
                advertisements = soup_res.find_all(['div', 'article'], selector)
            
            if advertisements:
                break
        
        logger.debug("Found %d advertisements on Imobiliare.ro page", len(advertisements))

        for adv in advertisements:
            try:
                # Extract title - look in multiple possible locations
                title_element = adv.find('h2') or adv.find('h3') or adv.find('a', class_=re.compile(r'.*title.*|.*titlu.*', re.IGNORECASE))
                
                title = title_element.get_text(strip=True) if isinstance(title_element, Tag) else ""
                if not title:
                    logger.debug("Skipping advertisement without title")
                    continue

                # Extract URL
                link_element = adv.find('a', href=True)
                if not isinstance(link_element, Tag):
                    logger.debug("Skipping advertisement without valid link")
                    continue
                
                url = link_element.get("href", "")
                if not url:
                    logger.debug("Skipping advertisement with empty URL")
                    continue
                    
                # Ensure URL is absolute
                if not url.startswith("http"):
                    url = "https://www.imobiliare.ro" + url

                # Extract ID from URL or data attribute
                ad_id = adv.get('data-listing-id') or adv.get('data-id')
                if not ad_id:
                    # Try to extract from URL
                    id_match = re.search(r'/(\d+)(?:/|$)', url)
                    if id_match:
                        ad_id = id_match.group(1)
                    else:
                        # Fallback: use last part of URL path
                        path_parts = url.rstrip('/').split('/')
                        ad_id = path_parts[-1] if path_parts else url
                
                # Create numeric ID from string ID
                processed_id = int(
                    hashlib.sha256(str(ad_id).encode('utf-8')).hexdigest(), 16
                ) % 10**16

                # Extract price
                price_element = adv.find(['span', 'div'], class_=re.compile(r'.*price.*|.*pret.*', re.IGNORECASE))
                if not price_element:
                    # Alternative: look for currency symbols
                    price_element = adv.find(string=re.compile(r'[€$]|\bEUR\b|\bRON\b'))
                    if price_element and isinstance(price_element.parent, Tag):
                        price_element = price_element.parent
                
                price = price_element.get_text(strip=True) if isinstance(price_element, Tag) else ""

                # Extract features (rooms, size)
                rooms = ""
                size = ""
                
                # Look for features container
                features_container = adv.find(['ul', 'div'], class_=re.compile(r'.*features.*|.*caracteristici.*', re.IGNORECASE))
                
                if isinstance(features_container, Tag):
                    features_text = features_container.get_text(" ", strip=True)
                    
                    # Look for rooms ("camere" in Romanian)
                    rooms_match = re.search(r'(\d+)\s*(?:camere|camera|cam\.?)', features_text, re.IGNORECASE)
                    if rooms_match:
                        rooms = rooms_match.group(1)
                    
                    # Look for size
                    size_match = re.search(r'(\d+)\s*(?:m[²p2]|mp)', features_text, re.IGNORECASE)
                    if size_match:
                        size = size_match.group(1)
                else:
                    # Fallback: search entire ad text
                    ad_text = adv.get_text(" ", strip=True)
                    rooms_match = re.search(r'(\d+)\s*(?:camere|camera|cam\.?)', ad_text, re.IGNORECASE)
                    if rooms_match:
                        rooms = rooms_match.group(1)
                    
                    size_match = re.search(r'(\d+)\s*(?:m[²p2]|mp)', ad_text, re.IGNORECASE)
                    if size_match:
                        size = size_match.group(1)

                # Extract image
                picture = adv.find("img")
                image = None
                if isinstance(picture, Tag):
                    # Try different attributes
                    image = picture.get('src') or picture.get('data-src') or picture.get('data-lazy-src')

                # Extract address/location
                location_element = adv.find(['span', 'div', 'p'], class_=re.compile(r'.*location.*|.*address.*|.*locatie.*|.*adresa.*', re.IGNORECASE))
                address = location_element.get_text(strip=True) if isinstance(location_element, Tag) else ""

                details = {
                    'id': processed_id,
                    'image': image,
                    'url': url,
                    'title': title,
                    'rooms': rooms,
                    'price': price,
                    'size': size,
                    'address': address,
                    'crawler': self.get_name()
                }
                entries.append(details)

            except Exception as e:  # pylint: disable=broad-except
                logger.warning("Error processing Imobiliare.ro advertisement: %s", str(e))
                continue

        logger.debug('Number of Imobiliare.ro entries found: %d', len(entries))
        return entries

    def load_address(self, url):
        """Extract address from Imobiliare.ro expose detail page"""
        try:
            soup = self.get_page(url, self.get_driver())
            
            # Try to find address in multiple possible locations
            address_element = soup.find(['div', 'span', 'p'], class_=re.compile(r'.*location.*|.*address.*|.*locatie.*|.*adresa.*', re.IGNORECASE))
            if not address_element:
                address_element = soup.find(['div', 'span', 'p'], attrs={"id": re.compile(r'.*location.*|.*address.*', re.IGNORECASE)})
            
            if isinstance(address_element, Tag):
                address = address_element.get_text(" ", strip=True)
                return address
            
            # Fallback: try meta tags
            meta_address = soup.find("meta", attrs={"property": "og:street-address"})
            if meta_address:
                return meta_address.get("content", "")
            
            meta_locality = soup.find("meta", attrs={"property": "og:locality"})
            if meta_locality:
                return meta_locality.get("content", "")
            
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Error extracting address from Imobiliare.ro: %s", str(e))
        
        return ""
