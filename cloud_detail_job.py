#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Detail scraper job for Google Cloud deployment.

This script runs as a scheduled job on Google Cloud Run to fetch detailed
information for Storia.ro and Imobiliare.ro listings.
"""

import os

from flathunter.argument_parser import parse
from flathunter.googlecloud_idmaintainer import GoogleCloudIdMaintainer
from flathunter.config import Config
from flathunter.logging import configure_logging, logger
from detail_scraper import DetailScraper

# Load config
args = parse()
config_handle = args.config
if config_handle is not None:
    config = Config(config_handle.name)
else:
    config = Config()

# Load the driver manager from local cache (if chrome_driver_install.py has been run)
os.environ['WDM_LOCAL'] = '1'

# Use Google Cloud DB
id_watch = GoogleCloudIdMaintainer(config)

configure_logging(config)

# Initialize search plugins for config
config.init_searchers()

# Get configuration
detail_config = config.get('detail_scraper', {})
hours_lookback = detail_config.get('hours_lookback', 24)

logger.info("Starting Google Cloud detail scraper job")

# Run the detail scraper once
scraper = DetailScraper(config, id_watch)
scraper.scrape_details(hours_lookback)

logger.info("Detail scraper job completed")
