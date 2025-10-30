#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Detail scraper for Storia and Imobiliare.ro listings.

This script runs independently from the main flathunter loop and periodically
fetches detailed information for saved listings from Storia.ro and Imobiliare.ro.
It enriches listings with:
- Full description text
- All photo URLs
- Construction year
- Floor/story number
- Building type
- Condition/state
- Heating type
- Parking information
"""

import time
import datetime
from datetime import time as dtime
from typing import List, Dict, Any

from flathunter.argument_parser import parse
from flathunter.logging import logger, configure_logging
from flathunter.idmaintainer import IdMaintainer
from flathunter.config import Config
from flathunter.crawler.storia import Storia
from flathunter.crawler.imobiliare_ro import ImobiliareRo
from flathunter.time_utils import get_random_time_jitter, wait_during_period

__author__ = "Flathunter Contributors"
__version__ = "1.0"
__status__ = "Production"


class DetailScraper:
    """Scrapes detailed information for saved listings"""

    def __init__(self, config: Config, id_watch: IdMaintainer):
        self.config = config
        self.id_watch = id_watch
        
        # Initialize crawlers for Storia and Imobiliare.ro
        self.storia_crawler = Storia(config)
        self.imobiliare_crawler = ImobiliareRo(config)
        
        # Map crawler names to crawler instances
        self.crawlers = {
            'Storia': self.storia_crawler,
            'ImobiliareRo': self.imobiliare_crawler
        }

    def get_listings_to_update(self, hours_ago: int = 24) -> List[Dict[str, Any]]:
        """Get listings from the last N hours that need detail updates"""
        min_datetime = datetime.datetime.now() - datetime.timedelta(hours=hours_ago)
        exposes = self.id_watch.get_exposes_since(min_datetime)
        
        # Filter for Storia and Imobiliare.ro listings only
        filtered = [
            expose for expose in exposes 
            if expose.get('crawler') in self.crawlers
        ]
        
        logger.info("Found %d listings to update (filtered from %d total)", 
                   len(filtered), len(exposes))
        return filtered

    def update_listing_details(self, expose: Dict[str, Any]) -> bool:
        """Fetch and update detailed information for a single listing"""
        crawler_name = expose.get('crawler')
        if not crawler_name or crawler_name not in self.crawlers:
            logger.debug("Skipping expose with crawler: %s", crawler_name)
            return False
        
        try:
            crawler = self.crawlers[crawler_name]
            logger.info("Fetching details for: %s (ID: %s, Crawler: %s)", 
                       expose.get('title', 'Unknown'), 
                       expose.get('id', 'Unknown'),
                       crawler_name)
            
            # Get detailed information
            updated_expose = crawler.get_expose_details(expose)
            
            # Check if we got new information
            new_fields = []
            for field in ['description', 'images', 'construction_year', 'floor', 
                         'building_type', 'condition', 'heating', 'parking']:
                if field in updated_expose and field not in expose:
                    new_fields.append(field)
                elif (field in updated_expose and field in expose and 
                      updated_expose[field] != expose[field]):
                    new_fields.append(field)
            
            if new_fields:
                logger.info("Updated fields: %s", ', '.join(new_fields))
                
                # Save updated expose to database
                self.id_watch.save_expose(updated_expose)
                return True
            else:
                logger.debug("No new details found for listing")
                return False
                
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error updating details for expose %s: %s", 
                        expose.get('url', 'unknown'), str(e))
            return False

    def scrape_details(self, hours_ago: int = 24):
        """Main scraping loop - fetch details for recent listings"""
        listings = self.get_listings_to_update(hours_ago)
        
        if not listings:
            logger.info("No listings to update")
            return
        
        updated_count = 0
        failed_count = 0
        
        for i, listing in enumerate(listings, 1):
            logger.info("Processing listing %d/%d", i, len(listings))
            
            if self.update_listing_details(listing):
                updated_count += 1
            else:
                failed_count += 1
            
            # Add delay between requests to avoid rate limiting
            if i < len(listings):  # Don't sleep after last item
                sleep_time = self.config.loop_period_seconds()
                if self.config.random_jitter_enabled():
                    sleep_time = get_random_time_jitter(sleep_time)
                
                logger.debug("Sleeping for %d seconds before next request", sleep_time)
                time.sleep(sleep_time)
        
        logger.info("Detail scraping complete: %d updated, %d failed/skipped", 
                   updated_count, failed_count)


def launch_detail_scraper(config: Config):
    """Starts the detail scraper loop"""
    id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')
    
    # Get loop configuration
    time_from = dtime.fromisoformat(config.loop_pause_from())
    time_till = dtime.fromisoformat(config.loop_pause_till())
    
    # Get detail scraper configuration
    detail_config = config.get('detail_scraper', {})
    hours_lookback = detail_config.get('hours_lookback', 24)
    loop_active = detail_config.get('loop_active', True)
    
    wait_during_period(time_from, time_till)
    
    scraper = DetailScraper(config, id_watch)
    scraper.scrape_details(hours_lookback)
    
    if not loop_active:
        logger.info("Detail scraper loop is disabled, exiting after single run")
        return
    
    # Main loop
    while True:
        wait_during_period(time_from, time_till)
        
        # Calculate sleep period
        if config.random_jitter_enabled():
            sleep_period = get_random_time_jitter(config.loop_period_seconds())
        else:
            sleep_period = config.loop_period_seconds()
        
        logger.info("Detail scraper sleeping for %d seconds", sleep_period)
        time.sleep(sleep_period)
        
        scraper.scrape_details(hours_lookback)


def main():
    """Processes command-line arguments, loads the config, launches the detail scraper"""
    # Load config
    args = parse()
    config_handle = args.config
    if config_handle is not None:
        config = Config(config_handle.name)
    else:
        config = Config()
    
    # Setup logging
    configure_logging(config)
    
    # Initialize search plugins for config
    config.init_searchers()
    
    logger.info("Starting detail scraper for Storia and Imobiliare.ro")
    
    # Start scraping details
    launch_detail_scraper(config)


if __name__ == "__main__":
    main()
