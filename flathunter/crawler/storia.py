"""Expose crawler for Storia.ro (Romanian real estate site)"""
import re
import datetime
import hashlib

from bs4 import BeautifulSoup, Tag

from flathunter.logging import logger
from flathunter.webdriver_crawler import WebdriverCrawler

class Storia(WebdriverCrawler):
    """Implementation of Crawler interface for Storia.ro"""

    URL_PATTERN = re.compile(r'https://www\.storia\.ro')

    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def get_page(self, search_url, driver=None, page_no=None):
        """Applies a page number to a formatted search URL and fetches the exposes at that page
        Storia.ro uses JavaScript rendering, so we always use the webdriver"""
        import time
        import random
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        driver = self.get_driver()
        if driver is None:
            logger.error("WebDriver not available for Storia.ro - Chrome is required")
            return BeautifulSoup("<html><body></body></html>", 'lxml')
        
        try:
            # Load the page
            driver.get(search_url)
            
            # Wait for Storia.ro specific content to load
            # Try multiple selectors to ensure the page has loaded
            try:
                # Wait for article listings OR listing container to appear
                WebDriverWait(driver, 15).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, 'article[data-cy="listing-item"]') or
                              d.find_elements(By.TAG_NAME, 'article') or
                              d.find_elements(By.CSS_SELECTOR, '[data-cy="search.listing"]')
                )
                logger.debug("Storia.ro: Content loaded successfully")
            except Exception as wait_error:
                logger.warning("Storia.ro: Timeout waiting for listings, trying anyway: %s", str(wait_error))
            
            # Additional wait for dynamic content with random jitter to appear more human
            time.sleep(random.uniform(2, 4))
            
            # Scroll to trigger lazy loading (Storia.ro uses lazy loading)
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
                logger.error("Storia.ro: CAPTCHA/bot detection triggered!")
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
                logger.warning("Storia.ro returned very short page (%d chars) - possible bot detection", len(page_source))
                logger.debug("Page source preview: %s", page_source[:500])
            else:
                logger.debug("Storia.ro: Retrieved page with %d characters", len(page_source))
            
            return BeautifulSoup(page_source, 'lxml')
            
        except Exception as e:
            logger.error("Error loading Storia.ro page: %s", str(e))
            return BeautifulSoup("<html><body></body></html>", 'lxml')

    def _populate_detail_from_soup(self, expose, soup):
        """Extract additional details from Storia.ro listing page"""
        expose = super()._populate_detail_from_soup(expose, soup)

        if soup is None:
            return expose

        # Set default availability date
        date = datetime.datetime.now().strftime("%d.%m.%Y")
        expose['from'] = date

        # Try to find availability date in the details
        # Storia.ro might have it in different places depending on listing type
        details_section = soup.find("div", attrs={"data-cy": "ad.top-information"})
        if isinstance(details_section, Tag):
            details_items = details_section.find_all("div", class_=re.compile(r"css-.*"))
            for item in details_items:
                text = item.get_text(strip=True).lower()
                if 'disponibil' in text or 'disponibilitate' in text:
                    # Extract date if present
                    date_match = re.search(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', text)
                    if date_match:
                        expose['from'] = date_match.group(0)
                    break

        # Extract description - Storia.ro uses specific structure
        description_container = soup.find("div", attrs={"data-cy": "ad.description"})
        if isinstance(description_container, Tag):
            text = description_container.get_text("\n", strip=True)
            if text:
                expose['description'] = text

        # Extract additional details from the characteristics section
        # Storia.ro lists property details in a structured format
        details_lists = soup.find_all("div", attrs={"data-cy": re.compile(r"ad\..*")})
        for details_list in details_lists:
            # Find all dt/dd pairs (definition lists)
            dt_elements = details_list.find_all("dt")
            dd_elements = details_list.find_all("dd")
            
            for dt, dd in zip(dt_elements, dd_elements):
                if not isinstance(dt, Tag) or not isinstance(dd, Tag):
                    continue
                    
                label = dt.get_text(strip=True).lower()
                value = dd.get_text(strip=True)
                
                # Extract construction year (Romanian: "Anul construcției")
                if 'anul' in label and 'construct' in label:
                    expose['construction_year'] = value
                
                # Extract floor (Romanian: "Etaj")
                if 'etaj' in label:
                    expose['floor'] = value
                
                # Extract building type (Romanian: "Tip construcție")
                if 'tip' in label and 'construct' in label:
                    expose['building_type'] = value
                
                # Extract condition/state (Romanian: "Stare")
                if 'stare' in label:
                    expose['condition'] = value
                
                # Extract heating type (Romanian: "Încălzire")
                if 'ncălzire' in label or 'incalzire' in label:
                    expose['heating'] = value
                
                # Extract parking (Romanian: "Parcare")
                if 'parcare' in label:
                    expose['parking'] = value

        # Extract images from gallery
        # Storia.ro typically uses a gallery component
        gallery = soup.find("div", attrs={"data-cy": "ad.gallery"})
        if not gallery:
            # Alternative location for gallery
            gallery = soup.find("div", class_=re.compile(r".*gallery.*", re.IGNORECASE))
        
        if isinstance(gallery, Tag):
            images = expose.get('images', [])
            
            # Check for picture elements (modern approach)
            for picture in gallery.find_all('picture'):
                img = picture.find('img')
                if isinstance(img, Tag):
                    # Try multiple attributes where image URL might be
                    for attr in ['src', 'data-src', 'srcset']:
                        url = img.get(attr)
                        if url:
                            # Handle srcset format (multiple URLs)
                            if attr == 'srcset':
                                url = url.split(',')[0].split(' ')[0]
                            clean_url = self._clean_image_url(url)
                            if clean_url and clean_url not in images:
                                images.append(clean_url)
                                break
            
            # Also check for direct img tags
            for img in gallery.find_all('img'):
                if isinstance(img, Tag):
                    for attr in ['src', 'data-src', 'data-original']:
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
        """Extracts all exposes from Storia.ro search results page"""
        entries = []
        soup_res = raw_data
        
        if not isinstance(soup_res, BeautifulSoup):
            logger.warning("Invalid soup object provided to Storia crawler")
            return []

        # Storia.ro uses article elements for listings
        # Find all articles - they don't have data-cy="listing-item" anymore
        advertisements = soup_res.find_all("article")
        
        # Filter to only articles that have listing links
        advertisements = [art for art in advertisements if art.find("a", attrs={"data-cy": "listing-item-link"})]

        logger.debug("Found %d advertisements on Storia.ro page", len(advertisements))

        for adv in advertisements:
            try:
                # Extract title using the new data-cy attribute
                title_element = adv.find("p", attrs={"data-cy": "listing-item-title"})
                if not title_element:
                    # Fallback to any header element
                    title_element = adv.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                
                title = title_element.get_text(strip=True) if isinstance(title_element, Tag) else ""
                if not title:
                    logger.debug("Skipping advertisement without title")
                    continue

                # Extract URL - should have data-cy="listing-item-link"
                link_element = adv.find("a", attrs={"data-cy": "listing-item-link"})
                if not link_element:
                    # Fallback: any link with /oferta/ in href
                    link_element = adv.find("a", href=re.compile(r"/oferta/"))
                
                if not isinstance(link_element, Tag):
                    logger.debug("Skipping advertisement without valid link")
                    continue
                
                url = link_element.get("href", "")
                if not url:
                    logger.debug("Skipping advertisement with empty URL")
                    continue
                    
                # Ensure URL is absolute
                if not url.startswith("http"):
                    url = "https://www.storia.ro" + url

                # Extract ID from URL
                # Format is usually /ro/oferta/...-ID<code>
                id_match = re.search(r'-ID([A-Za-z0-9]+)$', url)
                if id_match:
                    ad_id = id_match.group(1)
                else:
                    # Fallback: use last part of URL path
                    path_parts = url.rstrip('/').split('/')
                    ad_id = path_parts[-1] if path_parts else url
                
                processed_id = int(
                    hashlib.sha256(ad_id.encode('utf-8')).hexdigest(), 16
                ) % 10**16

                # Extract price - look for MainPrice data-sentry-element
                price_element = adv.find("span", attrs={"data-sentry-element": "MainPrice"})
                if not price_element:
                    # Fallback: look for any price-like element
                    price_element = adv.find("span", class_=re.compile(r".*price.*", re.IGNORECASE))
                price = price_element.get_text(strip=True) if isinstance(price_element, Tag) else ""

                # Extract features using DescriptionList
                features_container = adv.find("dl", attrs={"data-sentry-component": "DescriptionList"})
                
                rooms = ""
                size = ""
                
                if isinstance(features_container, Tag):
                    # Parse dt (term) and dd (definition) pairs
                    terms = features_container.find_all("dt")
                    definitions = features_container.find_all("dd")
                    
                    for term, definition in zip(terms, definitions):
                        term_text = term.get_text(strip=True).lower()
                        def_text = definition.get_text(strip=True)
                        
                        # Look for rooms ("Numărul de camere" in Romanian)
                        if 'camere' in term_text or 'camera' in term_text:
                            rooms = def_text
                        
                        # Look for size ("Prețul pe metru pătrat" or similar)
                        if 'm²' in def_text or 'm2' in def_text or 'mp' in def_text.lower():
                            size = def_text

                # Extract image - look for data-cy="listing-item-image-source"
                picture = adv.find("img", attrs={"data-cy": "listing-item-image-source"})
                if not picture:
                    # Fallback: any img tag
                    picture = adv.find("img")
                
                image = None
                if isinstance(picture, Tag):
                    # Try different attributes
                    image = picture.get('src') or picture.get('data-src') or picture.get('data-original')

                # Extract address - look for Address component
                location_element = adv.find("p", attrs={"data-sentry-component": "Address"})
                if not location_element:
                    # Fallback
                    location_element = adv.find("p", class_=re.compile(r".*address.*|.*location.*", re.IGNORECASE))
                
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
                logger.warning("Error processing Storia.ro advertisement: %s", str(e))
                continue

        logger.debug('Number of Storia.ro entries found: %d', len(entries))
        return entries

    def load_address(self, url):
        """Extract address from Storia.ro expose detail page"""
        try:
            soup = self.get_page(url, self.get_driver())
            
            # Try to find address in multiple possible locations
            address_element = soup.find("a", attrs={"data-cy": "ad.location"})
            if not address_element:
                address_element = soup.find("div", class_=re.compile(r".*location.*|.*address.*", re.IGNORECASE))
            
            if isinstance(address_element, Tag):
                address = address_element.get_text(" ", strip=True)
                return address
            
            # Fallback: try meta tags
            meta_address = soup.find("meta", attrs={"property": "og:street-address"})
            if meta_address:
                return meta_address.get("content", "")
            
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Error extracting address from Storia.ro: %s", str(e))
        
        return ""

