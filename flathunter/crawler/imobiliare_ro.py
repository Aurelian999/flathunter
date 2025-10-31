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
        import random
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
                # Wait for listing items to appear (reduced timeout from 300s to 45s)
                WebDriverWait(driver, 45).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, '.listing-card') or
                              d.find_elements(By.CSS_SELECTOR, '[data-cy*="listing-"]') or
                              d.find_elements(By.CSS_SELECTOR, '[id*="listing-"]') or
                              d.find_elements(By.CLASS_NAME, 'anunt')
                )
                logger.debug("Imobiliare.ro: Content loaded successfully")
            except Exception as wait_error:
                logger.warning("Imobiliare.ro: Timeout waiting for listings, trying anyway: %s", str(wait_error))
            
            # Additional wait for dynamic content with random jitter to appear more human
            time.sleep(random.uniform(2, 4))
            
            # Scroll to trigger lazy loading (Imobiliare.ro may use lazy loading)
            # Add random human-like scrolling behavior
            try:
                # Scroll to 25% of page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.25);")
                time.sleep(random.uniform(0.5, 1.5))
                
                # Scroll to 50% of page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(random.uniform(0.8, 1.8))
                
                # Scroll to 75% of page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.75);")
                time.sleep(random.uniform(0.5, 1.2))
                
                # Scroll to bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 2))
                
                # Scroll back up a bit (human behavior)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.8);")
                time.sleep(random.uniform(0.5, 1))
            except Exception as scroll_error:
                logger.debug("Could not scroll page: %s", str(scroll_error))
            
            # Get the page source after JavaScript execution
            page_source = driver.page_source
            
            # Check for bot detection / CAPTCHA
            if 'captcha-delivery.com' in page_source.lower() or 'please enable js' in page_source.lower():
                logger.error("Imobiliare.ro: CAPTCHA/bot detection triggered!")
                logger.error("Response preview: %s", page_source[:500])
                logger.info("Possible solutions:")
                logger.info("  1. Enable 'use_proxy_list: True' in config.yaml")
                logger.info("  2. Configure a CAPTCHA solver (Capmonster recommended)")
                logger.info("  3. Increase 'sleeping_time' in config.yaml")
                logger.info("  4. Wait a few hours before retrying")
                # Return empty soup to avoid processing error page
                return BeautifulSoup("<html><body></body></html>", 'lxml')
            
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

        # Extract additional property details
        # Imobiliare.ro lists property characteristics in various sections
        characteristics = soup.find_all(["ul", "div"], class_=re.compile(r".*caracteristici.*|.*features.*|.*details.*", re.IGNORECASE))
        
        for char_section in characteristics:
            if not isinstance(char_section, Tag):
                continue
            
            # Look for list items or divs with label-value pairs
            items = char_section.find_all(["li", "div", "span"])
            
            for item in items:
                if not isinstance(item, Tag):
                    continue
                    
                text = item.get_text(strip=True).lower()
                
                # Extract construction year (Romanian: "An construcție")
                if 'an' in text and 'construct' in text:
                    year_match = re.search(r'\b(19|20)\d{2}\b', text)
                    if year_match:
                        expose['construction_year'] = year_match.group(0)
                
                # Extract floor (Romanian: "Etaj")
                if 'etaj' in text:
                    # Try to extract floor number
                    floor_match = re.search(r'etaj\s*[:|-]?\s*(\d+|parter|mansardă)', text, re.IGNORECASE)
                    if floor_match:
                        expose['floor'] = floor_match.group(1)
                
                # Extract building type (Romanian: "Tip construcție")
                if 'tip' in text and ('construct' in text or 'clădire' in text):
                    # Extract value after the label
                    value_match = re.search(r'tip.*?[:|-]\s*(.+?)(?:\||$)', text, re.IGNORECASE)
                    if value_match:
                        expose['building_type'] = value_match.group(1).strip()
                
                # Extract condition/state (Romanian: "Stare")
                if 'stare' in text and 'imobil' in text:
                    value_match = re.search(r'stare.*?[:|-]\s*(.+?)(?:\||$)', text, re.IGNORECASE)
                    if value_match:
                        expose['condition'] = value_match.group(1).strip()
                
                # Extract heating type (Romanian: "Sistem încălzire")
                if 'încălzire' in text or 'incalzire' in text:
                    value_match = re.search(r'(?:sistem\s+)?(?:î|i)ncălzire.*?[:|-]\s*(.+?)(?:\||$)', text, re.IGNORECASE)
                    if value_match:
                        expose['heating'] = value_match.group(1).strip()
                
                # Extract parking (Romanian: "Parcare")
                if 'parcare' in text or 'garaj' in text:
                    expose['parking'] = text

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
                            # Simple URL cleaning
                            if url and 'default-card-thumbnail' not in url:
                                if url.startswith('//'):
                                    url = 'https:' + url
                                elif not url.startswith('http'):
                                    url = 'https://www.imobiliare.ro' + url if url.startswith('/') else url
                                if url and url not in images:
                                    images.append(url)
                                    break
            
            # Also check for direct img tags
            for img in gallery.find_all('img'):
                if isinstance(img, Tag):
                    for attr in ['src', 'data-src', 'data-original', 'data-lazy-src']:
                        url = img.get(attr)
                        if url and 'default-card-thumbnail' not in url:
                            if url.startswith('//'):
                                url = 'https:' + url
                            elif not url.startswith('http'):
                                url = 'https://www.imobiliare.ro' + url if url.startswith('/') else url
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
        
        # Try new selectors for the updated Imobiliare.ro structure
        for selector in [
            {'class': re.compile(r'listing-card')},
            {'attrs': {'data-cy': re.compile(r'listing-\d+')}},
            {'attrs': {'id': re.compile(r'listing-\d+')}},
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
                title_element = adv.find('span', class_='line-clamp-2') or \
                               adv.find('h3', class_=re.compile(r'.*text-black.*')) or \
                               adv.find('h3') or \
                               adv.find('a', class_=re.compile(r'.*title.*|.*titlu.*', re.IGNORECASE))
                
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
                price_element = adv.find('div', class_=re.compile(r'.*text-grey-900.*')) or \
                               adv.find(['span', 'div'], class_=re.compile(r'.*price.*|.*pret.*', re.IGNORECASE)) or \
                               adv.find(string=re.compile(r'[€$]|\bEUR\b|\bRON\b'))
                if price_element and isinstance(price_element, Tag):
                    price = price_element.get_text(strip=True)
                elif price_element:
                    # Handle case where price_element is a NavigableString
                    price = str(price_element).strip()
                else:
                    price = ""

                # Extract features (rooms, size)
                rooms = ""
                size = ""
                
                # Look for features with data-cy attributes (new structure)
                bedroom_element = adv.find('span', attrs={'data-cy': 'card-bedroom_count'})
                if isinstance(bedroom_element, Tag):
                    bedroom_text = bedroom_element.get_text(strip=True)
                    rooms_match = re.search(r'(\d+)', bedroom_text)
                    if rooms_match:
                        rooms = rooms_match.group(1)
                
                surface_element = adv.find('span', attrs={'data-cy': 'card-usable_surface'})
                if isinstance(surface_element, Tag):
                    surface_text = surface_element.get_text(strip=True)
                    size_match = re.search(r'(\d+(?:\.\d+)?)', surface_text)
                    if size_match:
                        size = size_match.group(1)
                
                # Fallback: search entire ad text for old structure
                if not rooms or not size:
                    ad_text = adv.get_text(" ", strip=True)
                    if not rooms:
                        rooms_match = re.search(r'(\d+)\s*(?:camere|camera|cam\.?)', ad_text, re.IGNORECASE)
                        if rooms_match:
                            rooms = rooms_match.group(1)
                    
                    if not size:
                        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m[²p2]|mp)', ad_text, re.IGNORECASE)
                        if size_match:
                            size = size_match.group(1)

                # Extract image
                picture = adv.find("img")
                image = None
                if isinstance(picture, Tag):
                    # Try different attributes
                    image = picture.get('src') or picture.get('data-src') or picture.get('data-lazy-src')
                    
                    # Clean up the image URL if it exists
                    if image and 'default-card-thumbnail' not in image:
                        # Simple URL cleaning - ensure it's absolute and remove query params if needed
                        if image.startswith('//'):
                            image = 'https:' + image
                        elif not image.startswith('http'):
                            image = 'https://www.imobiliare.ro' + image if image.startswith('/') else image

                # Extract address/location
                location_element = adv.find('p', class_=re.compile(r'.*truncate.*')) or \
                                  adv.find(['span', 'div', 'p'], class_=re.compile(r'.*location.*|.*address.*|.*locatie.*|.*adresa.*', re.IGNORECASE))
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
