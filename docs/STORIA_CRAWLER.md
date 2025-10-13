# Storia.ro Crawler Documentation

## Overview

The Storia.ro crawler (`flathunter/crawler/storia.py`) is designed to scrape rental property listings from [Storia.ro](https://www.storia.ro), Romania's popular real estate marketplace.

## Features

### Search Results Extraction
The crawler extracts the following information from search result pages:
- **Title**: Property listing title
- **Price**: Rental price (in RON or EUR)
- **Size**: Property size in square meters
- **Rooms**: Number of rooms (camere)
- **Address**: Location/address information
- **Image**: Thumbnail image from listing
- **URL**: Direct link to the full listing

### Detail Page Enhancement
When visiting individual listing pages, the crawler also extracts:
- **Full Description**: Complete property description text
- **Image Gallery**: All available photos from the listing
- **Availability Date**: When the property becomes available (if specified)

## Configuration

### URL Format
Add Storia.ro search URLs to your `config.yaml`:

```yaml
urls:
  - https://www.storia.ro/ro/rezultate/inchiriere/apartament/bucuresti?limit=36
  - https://www.storia.ro/ro/rezultate/inchiriere/casa/cluj-napoca
```

### Supported Search Types
- Apartments (apartament)
- Houses (casa)
- Rooms (camera)
- Studios (garsoniera)

### Search Parameters
Storia.ro URLs can include various filters:
- Location: `/bucuresti`, `/cluj-napoca`, etc.
- Price range: `?price_from=XXX&price_to=YYY`
- Size range: `?surface_from=XX&surface_to=YY`
- Number of rooms: `?no_of_rooms=X`

## Technical Details

### WebDriver-Based Crawling
Storia.ro uses **WebdriverCrawler** (like Kleinanzeigen and ImmoScout24) instead of basic requests:
- Uses headless Chrome browser to handle JavaScript-rendered content
- Better handling of bot detection and dynamic content
- Requires Chrome/Chromium to be installed on the system
- Can solve CAPTCHAs if configured with captcha solving services

### HTML Structure
The crawler is designed to handle Storia.ro's modern HTML structure:
- **Listings**: Uses `<article>` elements with `data-cy="listing-item"` attributes
- **Features**: Extracts details from `data-cy="listing-item-features"` sections
- **Gallery**: Looks for `data-cy="ad.gallery"` on detail pages
- **Description**: Extracts from `data-cy="ad.description"` containers

### Fallback Mechanisms
The crawler includes fallback strategies for:
- Alternative CSS class patterns when data-cy attributes are missing
- Multiple image source attributes (src, data-src, srcset)
- Flexible ID extraction from URLs
- Various location element patterns

### Romanian Language Support
The crawler recognizes Romanian property terminology:
- "camere" / "camera" for room count
- "mp" / "m²" for square meters
- "disponibil" / "disponibilitate" for availability dates

## Testing

Run the Storia.ro crawler tests:

```bash
pytest test/crawler/test_crawl_storia.py
```

## Integration

The crawler is automatically initialized in `flathunter/config.py` along with other supported sites. No additional configuration is needed beyond adding Storia.ro URLs to your search list.

## Example Configuration

```yaml
urls:
  - https://www.storia.ro/ro/rezultate/inchiriere/apartament/bucuresti?limit=36&price_to=500

filters:
  min_rooms: 2
  max_price: 2500
  min_size: 50

notifiers:
  - telegram

telegram:
  bot_token: YOUR_BOT_TOKEN
  receiver_ids:
    - YOUR_CHAT_ID
```

## Notes

### Bot Detection
Storia.ro may implement anti-bot measures. If you encounter issues:
- Enable proxy rotation: `use_proxy_list: true`
- Adjust crawl intervals in loop settings
- Consider using headless browser mode if needed

### Data Accuracy
- Price formats may vary (RON vs EUR)
- Room counts may be approximate
- Address precision depends on listing quality
- Images are extracted from available sources

## Future Enhancements

Potential improvements for the Storia.ro crawler:
- Enhanced date parsing for Romanian date formats
- Better handling of featured/promoted listings
- Support for commercial properties
- Integration with Storia.ro's filtering system
- Multilingual support (Romanian/English interface)

