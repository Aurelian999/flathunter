# Detail Scraper for Storia and Imobiliare.ro

## Overview

The Detail Scraper is an independent component that periodically fetches detailed information for saved listings from Storia.ro and Imobiliare.ro. It runs separately from the main Flathunter scraper and enriches listing data with:

- **Full description text**: Complete property description
- **All photos**: Complete gallery of property images
- **Construction year**: When the building was built
- **Floor/Story**: Which floor the property is on
- **Building type**: Type of construction (e.g., brick, concrete)
- **Condition**: Property state (new, renovated, needs renovation)
- **Heating type**: Heating system information
- **Parking**: Parking availability

## Why a Separate Scraper?

The main Flathunter scraper focuses on quickly finding new listings from search result pages. The Detail Scraper runs independently to:

1. **Avoid slowing down main scraper**: Fetching detail pages is time-consuming
2. **Reduce rate limiting**: Spreads requests over time
3. **Enable flexible scheduling**: Can run on different intervals than main scraper
4. **Provide richer data**: Extracts additional fields not available on search pages

## Configuration

Add the following to your `config.yaml`:

```yaml
detail_scraper:
  loop_active: yes  # Should the detail scraper loop endlessly?
  hours_lookback: 24  # How many hours back to look for listings to update
```

### Configuration Options

- `loop_active` (default: `yes`): Whether to continuously loop or run once
- `hours_lookback` (default: `24`): How far back to look for listings to update

The detail scraper uses the same `loop.sleeping_time` and `loop.random_jitter` settings as the main scraper.

## Running Locally

### Command Line

Run the detail scraper as a standalone process:

```bash
python detail_scraper.py
```

With custom config:

```bash
python detail_scraper.py --config /path/to/config.yaml
```

### Single Run (No Loop)

To run once and exit, set in your config:

```yaml
detail_scraper:
  loop_active: no
```

### As a Service

Use the provided systemd service file:

```bash
# Edit the service file with your paths
sudo cp sample-detail-scraper.service /etc/systemd/system/detail-scraper.service
sudo nano /etc/systemd/system/detail-scraper.service

# Enable and start the service
sudo systemctl enable detail-scraper.service
sudo systemctl start detail-scraper.service

# Check status
sudo systemctl status detail-scraper.service
```

## Google Cloud Deployment

### Option 1: Scheduled Cloud Run Job

1. Build the Docker image:

```bash
docker build -f Dockerfile.detail-scraper -t gcr.io/YOUR-PROJECT/flathunter-detail-scraper .
docker push gcr.io/YOUR-PROJECT/flathunter-detail-scraper
```

2. Create a Cloud Run job:

```bash
gcloud run jobs create flathunter-detail-scraper \
  --image gcr.io/YOUR-PROJECT/flathunter-detail-scraper \
  --region us-central1 \
  --memory 1Gi \
  --cpu 1
```

3. Create a Cloud Scheduler job:

```bash
gcloud scheduler jobs create http detail-scraper-schedule \
  --location us-central1 \
  --schedule "0 */1 * * *" \
  --uri "https://REGION-PROJECT.cloudfunctions.net/scrape-details" \
  --http-method GET
```

### Option 2: Cron Job via App Engine

The detail scraper is automatically configured in `cron.yaml`:

```yaml
- description: "Scrape listing details for Storia and Imobiliare.ro"
  url: /scrape-details
  schedule: every 1 hours synchronized
```

Deploy to App Engine:

```bash
gcloud app deploy app.yaml cron.yaml
```

The `/scrape-details` endpoint will be called hourly to fetch listing details.

## How It Works

1. **Query Database**: Loads listings from the last N hours (configurable)
2. **Filter by Crawler**: Only processes Storia and Imobiliare.ro listings
3. **Fetch Details**: Calls `get_expose_details()` for each listing
4. **Extract Data**: Parses HTML to extract detailed information
5. **Update Database**: Saves enriched data back to the database
6. **Rate Limiting**: Waits between requests to avoid being blocked

## Database Storage

Detailed information is stored in the `exposes` table with the same structure as main listings. New fields are added:

- `description`: Full property description
- `images`: Array of all image URLs
- `construction_year`: Building construction year
- `floor`: Floor/story number
- `building_type`: Type of building
- `condition`: Property condition
- `heating`: Heating system type
- `parking`: Parking information

## Accessing Detailed Data

### Via Web Interface

Detailed information is automatically available in the web interface when viewing listings.

### Via API

```python
from flathunter.idmaintainer import IdMaintainer
from flathunter.config import Config

config = Config()
id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')

# Get recent listings with details
exposes = id_watch.get_recent_exposes(count=10)

for expose in exposes:
    print(f"Title: {expose['title']}")
    print(f"Description: {expose.get('description', 'N/A')}")
    print(f"Images: {len(expose.get('images', []))}")
    print(f"Construction Year: {expose.get('construction_year', 'N/A')}")
    print(f"Floor: {expose.get('floor', 'N/A')}")
    print()
```

## Logging

The detail scraper logs all operations:

```
INFO: Starting detail scraper for Storia and Imobiliare.ro
INFO: Found 15 listings to update (filtered from 50 total)
INFO: Processing listing 1/15
INFO: Fetching details for: Apartament 3 camere Bucuresti (ID: 12345, Crawler: ImobiliareRo)
INFO: Updated fields: description, images, construction_year, floor
INFO: Detail scraping complete: 12 updated, 3 failed/skipped
```

## Troubleshooting

### No listings being updated

- Check that you have Storia or Imobiliare.ro URLs in your config
- Verify listings exist in the database within the lookback period
- Check the `crawler` field matches "Storia" or "ImobiliareRo"

### Rate limiting / blocked requests

- Increase `loop.sleeping_time` to add more delay between requests
- Enable `loop.random_jitter` to randomize request timing
- Configure proxy rotation with `use_proxy_list: true`
- Consider using a CAPTCHA solver

### Missing fields in results

The detail scraper does its best to extract fields, but some may not be available:
- Not all listings have all fields
- Website HTML structure may change over time
- Some fields may be behind login walls

### Chrome driver issues

Ensure Chrome and ChromeDriver are properly installed:

```bash
python chrome_driver_install.py
```

## Performance Considerations

### Memory Usage

- Each crawler maintains a Chrome WebDriver instance (~200MB RAM)
- Consider processing in batches if you have many listings

### Execution Time

- Fetching details is slower than search results (~5-10 seconds per listing)
- With 100 listings and 600 second sleep time, expect ~16 hours per cycle
- Adjust `sleeping_time` and `hours_lookback` based on your needs

### Cost (Google Cloud)

- Cloud Run job: ~$0.0004 per second of execution
- With 100 listings at 10 seconds each: ~$0.40 per run
- Hourly runs: ~$300/month (can be reduced with less frequent scheduling)

## Best Practices

1. **Start with manual testing**: Run once locally to verify it works
2. **Monitor logs**: Check for rate limiting or errors
3. **Adjust timing**: Find the right balance between freshness and rate limits
4. **Use proxies for high volume**: Enable proxy rotation if processing many listings
5. **Set reasonable lookback**: Don't fetch details for very old listings

## Integration with Main Scraper

The detail scraper is completely independent:

- Main scraper: Finds new listings, sends notifications
- Detail scraper: Enriches existing listings with full data

Both can run simultaneously without interfering with each other.

## Example Workflow

1. **Main Scraper** (every 10 minutes):
   - Searches for new listings
   - Saves basic info to database
   - Sends Telegram notification

2. **Detail Scraper** (every hour):
   - Loads listings from last 24 hours
   - Fetches full details for each
   - Updates database with rich data

3. **User**:
   - Receives quick notification from main scraper
   - Views full details in web interface (from detail scraper)

## Support

For issues or questions:
- Check logs for error messages
- Review [STORIA_IMPLEMENTATION.md](../STORIA_IMPLEMENTATION.md)
- Review [IMOBILIARE_RO_IMPLEMENTATION.md](../IMOBILIARE_RO_IMPLEMENTATION.md)
- Open an issue on GitHub
