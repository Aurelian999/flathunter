# Imobiliare.ro Crawler

## Overview

The Imobiliare.ro crawler is a WebDriver-based scraper designed to extract property listings from [Imobiliare.ro](https://www.imobiliare.ro), a major Romanian real estate platform.

## Features

- **WebDriver-based crawling**: Uses headless Chrome to handle JavaScript-rendered content
- **Flexible HTML parsing**: Multiple fallback selectors for robustness
- **Romanian language support**: Recognizes Romanian real estate terminology
- **Comprehensive data extraction**: Extracts title, price, size, rooms, location, and images
- **Detail page enhancement**: Fetches full descriptions and photo galleries from listing detail pages

## Configuration

Add Imobiliare.ro URLs to your `config.yaml`:

```yaml
urls:
  - https://www.imobiliare.ro/vanzare-apartamente/bucuresti
  - https://www.imobiliare.ro/inchirieri-apartamente/cluj-napoca
```

### Search URL Examples

**Bucharest - Apartments for Sale:**
```
https://www.imobiliare.ro/vanzare-apartamente/bucuresti
```

**Cluj-Napoca - Apartments for Rent:**
```
https://www.imobiliare.ro/inchirieri-apartamente/cluj-napoca
```

**Timisoara - Houses for Sale:**
```
https://www.imobiliare.ro/vanzare-case-vile/timisoara
```

## Filters

Apply filters to narrow down your search:

```yaml
filters:
  min_rooms: 2
  max_rooms: 4
  min_size: 50
  max_size: 100
  min_price: 50000
  max_price: 150000
```

## Technical Details

### Extracted Data

From search results pages, the crawler extracts:
- **ID**: Unique identifier (hash-based from listing ID)
- **Title**: Property title
- **Price**: Listed price (in RON or EUR)
- **Rooms**: Number of rooms
- **Size**: Property size in square meters (m²)
- **Address**: Location/neighborhood
- **Image**: Thumbnail image URL
- **URL**: Link to full listing

### HTML Selectors

The crawler supports multiple HTML patterns commonly used on Romanian real estate sites:

**Listing containers:**
- `.listing-item`
- `.property-item`
- `.anunt`
- `[data-listing-id]`

**Features:**
- Rooms: Pattern matches `(\d+)\s*(?:camere|camera|cam\.?)`
- Size: Pattern matches `(\d+)\s*(?:m[²p2]|mp)`

### Detail Page Enhancement

When `resolve_addresses` is enabled, the crawler fetches additional details from listing pages:
- Full description text
- Complete photo gallery
- Availability date (if specified)

## Romanian Terminology

The crawler recognizes common Romanian real estate terms:

| Romanian | English | Pattern |
|----------|---------|---------|
| camere/camera | rooms | `\d+ camere` |
| m²/mp | square meters | `\d+ m²` |
| disponibil | available | Text search |
| descriere | description | Class/ID search |
| pret | price | Class search |
| locatie/adresa | location/address | Class search |

## Requirements

### Dependencies
- Chrome/Chromium browser
- Selenium WebDriver
- BeautifulSoup4
- undetected-chromedriver

### Configuration Options

```yaml
# Enable Chrome WebDriver (required for Imobiliare.ro)
# Chrome is automatically used by WebdriverCrawler

# Optional: Use proxy if facing bot detection
use_proxy_list: false

# Recommended loop interval
loop:
  sleeping_time: 600  # 10 minutes
  random_jitter: true
```

## Bot Detection

Imobiliare.ro may implement bot detection measures. To improve reliability:

1. **Use reasonable polling intervals**: Set `sleeping_time` to 600+ seconds
2. **Enable random jitter**: Adds variability to request timing
3. **Consider proxies**: Enable `use_proxy_list: true` if you encounter issues
4. **Headless Chrome**: The crawler uses undetected-chromedriver to avoid detection

## Notifications

Configure notifications to receive alerts for new listings:

```yaml
notifiers:
  - telegram

telegram:
  bot_token: YOUR_BOT_TOKEN
  receiver_ids:
    - YOUR_CHAT_ID
  notify_with_images: true
```

Example notification message:

```
🏠 Apartament 3 camere Bucuresti

📍 Bucuresti, Sector 1
💰 €120,000
📐 75 m²
🚪 3 camere

🔗 https://www.imobiliare.ro/anunt/...
```

## Troubleshooting

### No Listings Found

**Problem**: Crawler returns empty results

**Solutions**:
1. Check if the URL is accessible in a browser
2. Verify Chrome/Chromium is installed
3. Check logs for bot detection warnings
4. Try enabling proxy support

### Bot Detection Errors

**Problem**: Page returns very short content or captcha

**Solutions**:
1. Increase `sleeping_time` to 900+ seconds
2. Enable `use_proxy_list: true`
3. Use Chrome instead of Chromium
4. Check if Imobiliare.ro has updated their anti-bot measures

### Missing Data Fields

**Problem**: Some properties missing price, size, or rooms

**Solutions**:
This is normal - not all listings include complete information. The crawler extracts available data and leaves missing fields as empty strings.

## Testing

Run the test suite:

```bash
pytest test/crawler/test_crawl_imobiliare_ro.py -v
```

Test with a live URL (requires Chrome):

```bash
pytest test/crawler/test_crawl_imobiliare_ro.py::test_process_expose_fetches_details -v -s
```

## Integration Example

Complete configuration example:

```yaml
# Imobiliare.ro configuration example
urls:
  - https://www.imobiliare.ro/vanzare-apartamente/bucuresti

loop:
  active: true
  sleeping_time: 600
  random_jitter: true

filters:
  min_rooms: 2
  max_rooms: 3
  min_size: 50
  max_size: 85
  max_price: 120000
  excluded_titles:
    - "demisol"
    - "subsol"

notifiers:
  - telegram

telegram:
  bot_token: YOUR_TELEGRAM_BOT_TOKEN
  receiver_ids:
    - YOUR_CHAT_ID
  notify_with_images: true

google_maps_api:
  key: YOUR_GOOGLE_MAPS_API_KEY

resolve_addresses: true
```

## Comparison with Storia.ro

Both Imobiliare.ro and Storia.ro are Romanian real estate platforms:

| Feature | Imobiliare.ro | Storia.ro |
|---------|---------------|-----------|
| WebDriver | ✓ Required | ✓ Required |
| JavaScript | ✓ Heavy | ✓ Heavy |
| Lazy Loading | ✓ Yes | ✓ Yes |
| Bot Detection | Moderate | Moderate |
| Data Quality | Good | Good |

**Recommendation**: Use both crawlers for comprehensive coverage of the Romanian property market.

## Support

For issues specific to the Imobiliare.ro crawler:
1. Check the [main README](../README.md) for general Flathunter setup
2. Review logs for specific error messages
3. Test with the provided unit tests
4. Open an issue on GitHub with crawler-specific tag

## Credits

This crawler was developed following the architecture established by the Storia.ro crawler, adapted for Imobiliare.ro's specific HTML structure and data patterns.
