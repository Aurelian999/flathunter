# Quick Start: Detail Scraper for Storia & Imobiliare.ro

Get up and running with the detail scraper in 5 minutes!

## Prerequisites

- Python 3.10+
- Chrome/Chromium browser
- Flathunter already installed and configured

## Step 1: Configure

Add to your `config.yaml`:

```yaml
detail_scraper:
  loop_active: yes
  hours_lookback: 24
```

Make sure you have Storia.ro or Imobiliare.ro URLs in your config:

```yaml
urls:
  - https://www.storia.ro/ro/rezultate/inchiriere/apartament/bucuresti
  - https://www.imobiliare.ro/inchirieri-apartamente/bucuresti
```

## Step 2: Run Main Scraper First

The detail scraper needs listings to work with. Run the main scraper to collect some listings:

```bash
python flathunt.py
```

Wait for it to find a few listings (you'll see them in Telegram notifications).

## Step 3: Run Detail Scraper

In a separate terminal, start the detail scraper:

```bash
python detail_scraper.py
```

You'll see output like:

```
INFO: Starting detail scraper for Storia and Imobiliare.ro
INFO: Found 5 listings to update (filtered from 12 total)
INFO: Processing listing 1/5
INFO: Fetching details for: Apartament 3 camere Bucuresti (ID: 12345, Crawler: Storia)
INFO: Updated fields: description, images, construction_year, floor
...
INFO: Detail scraping complete: 5 updated, 0 failed/skipped
```

## Step 4: View Results

Check the database or web interface to see the enriched data:

```python
from flathunter.config import Config
from flathunter.idmaintainer import IdMaintainer

config = Config()
id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')

# Get recent listings
exposes = id_watch.get_recent_exposes(count=5)

for expose in exposes:
    print(f"\n{expose['title']}")
    if 'description' in expose:
        print(f"Description: {expose['description'][:100]}...")
    if 'images' in expose:
        print(f"Images: {len(expose['images'])}")
    if 'construction_year' in expose:
        print(f"Built: {expose['construction_year']}")
```

## What Gets Extracted?

For each listing, the detail scraper fetches:

✅ **Full description** - Complete property description  
✅ **All photos** - Every image from the gallery  
✅ **Construction year** - When the building was built  
✅ **Floor** - Which floor the property is on  
✅ **Building type** - Construction material (brick, concrete, etc.)  
✅ **Condition** - New, renovated, needs work, etc.  
✅ **Heating** - Type of heating system  
✅ **Parking** - Parking availability  

## Scheduling (Optional)

### Option 1: Run Manually

Just run `python detail_scraper.py` whenever you want to update details.

### Option 2: Systemd Service

Copy and configure the service file:

```bash
sudo cp sample-detail-scraper.service /etc/systemd/system/
sudo systemctl enable detail-scraper.service
sudo systemctl start detail-scraper.service
```

### Option 3: Cron Job

Add to your crontab:

```bash
# Run detail scraper every hour
0 * * * * cd /path/to/flathunter && python detail_scraper.py
```

For single-run mode (recommended for cron), set in config:

```yaml
detail_scraper:
  loop_active: no  # Exit after one run
  hours_lookback: 24
```

## Troubleshooting

### "No listings to update"

- Make sure main scraper has found some Storia/Imobiliare.ro listings
- Check that `hours_lookback` is long enough
- Verify URLs are configured correctly

### Chrome/WebDriver errors

Install Chrome driver:

```bash
python chrome_driver_install.py
```

### Rate limiting

If you're being blocked:

1. Increase `sleeping_time` in config
2. Enable `random_jitter: True`
3. Consider using proxy rotation
4. Reduce `hours_lookback` to process fewer listings

## Next Steps

- Read the [full documentation](DETAIL_SCRAPER.md)
- Deploy to [Google Cloud](DETAIL_SCRAPER.md#google-cloud-deployment)
- Customize [message templates](../README.md#configuration) to include new fields
- Check [performance tips](DETAIL_SCRAPER.md#performance-considerations)

## Example Config

See `examples/config.detail_scraper.yaml` for a complete configuration example.

## Need Help?

- Check logs for error messages
- Review [STORIA_IMPLEMENTATION.md](../STORIA_IMPLEMENTATION.md)
- Review [IMOBILIARE_RO_IMPLEMENTATION.md](../IMOBILIARE_RO_IMPLEMENTATION.md)
- Open an issue on GitHub
