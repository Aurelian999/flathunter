#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example usage of the detail scraper

This script demonstrates how to use the detail scraper programmatically
to fetch detailed information for Storia and Imobiliare.ro listings.
"""

from flathunter.config import Config
from flathunter.idmaintainer import IdMaintainer
from detail_scraper import DetailScraper


def example_detail_scraping():
    """Example: Fetch details for recent listings"""
    # Load configuration
    config = Config('config.yaml')
    
    # Initialize database connection
    id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')
    
    # Create detail scraper
    scraper = DetailScraper(config, id_watch)
    
    # Fetch details for listings from the last 24 hours
    print("Fetching details for listings from last 24 hours...")
    scraper.scrape_details(hours_ago=24)
    
    print("Detail scraping complete!")


def example_access_detailed_data():
    """Example: Access detailed data from database"""
    # Load configuration
    config = Config('config.yaml')
    
    # Initialize database connection
    id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')
    
    # Get recent listings with details
    print("Loading recent listings...")
    exposes = id_watch.get_recent_exposes(count=10)
    
    for expose in exposes:
        print(f"\n{'='*80}")
        print(f"Title: {expose['title']}")
        print(f"Crawler: {expose.get('crawler', 'Unknown')}")
        print(f"URL: {expose.get('url', 'N/A')}")
        
        # Display detailed information if available
        if 'description' in expose:
            desc = expose['description'][:100] + "..." if len(expose['description']) > 100 else expose['description']
            print(f"Description: {desc}")
        
        if 'images' in expose:
            print(f"Number of images: {len(expose['images'])}")
        
        if 'construction_year' in expose:
            print(f"Construction year: {expose['construction_year']}")
        
        if 'floor' in expose:
            print(f"Floor: {expose['floor']}")
        
        if 'building_type' in expose:
            print(f"Building type: {expose['building_type']}")
        
        if 'condition' in expose:
            print(f"Condition: {expose['condition']}")
        
        if 'heating' in expose:
            print(f"Heating: {expose['heating']}")
        
        if 'parking' in expose:
            print(f"Parking: {expose['parking']}")


def example_update_single_listing():
    """Example: Update details for a specific listing"""
    # Load configuration
    config = Config('config.yaml')
    
    # Initialize database connection
    id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')
    
    # Create detail scraper
    scraper = DetailScraper(config, id_watch)
    
    # Example expose (in reality, you'd fetch this from the database)
    expose = {
        'id': 12345,
        'crawler': 'Storia',
        'url': 'https://www.storia.ro/ro/oferta/apartament-3-camere-ID123ABC',
        'title': 'Apartament 3 camere Bucuresti',
        'price': '€120,000',
        'size': '75',
        'rooms': '3'
    }
    
    print(f"Fetching details for: {expose['title']}")
    
    # Update the listing with detailed information
    success = scraper.update_listing_details(expose)
    
    if success:
        print("Successfully updated listing with detailed information!")
    else:
        print("Failed to fetch additional details")


if __name__ == "__main__":
    print("Detail Scraper Examples")
    print("=" * 80)
    
    # Choose which example to run
    # Uncomment the example you want to try:
    
    # Example 1: Scrape details for recent listings
    # example_detail_scraping()
    
    # Example 2: Access detailed data from database
    # example_access_detailed_data()
    
    # Example 3: Update a single listing
    # example_update_single_listing()
    
    print("\nTo use these examples, uncomment the desired function call in __main__")
