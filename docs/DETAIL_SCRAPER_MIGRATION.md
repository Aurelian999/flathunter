# Migration Guide: Enabling Detail Scraper

This guide helps existing Flathunter users add the detail scraper to their setup.

## Who Should Use This?

If you're already using Flathunter with Storia.ro or Imobiliare.ro URLs and want to get:
- Full property descriptions (not just titles)
- Complete photo galleries (all images, not just thumbnails)
- Additional property details (construction year, floor, etc.)

Then the detail scraper is for you!

## Prerequisites

- Flathunter already installed and working
- At least one Storia.ro or Imobiliare.ro URL in your config
- Main scraper has collected at least a few listings

## Migration Steps

### 1. Update Your Config

Add the detail scraper section to your `config.yaml`:

```yaml
# Add this section anywhere in your config file
detail_scraper:
  loop_active: yes  # Set to 'no' if you want to run it manually/via cron
  hours_lookback: 24  # Process listings from last 24 hours
```

### 2. Test with a Single Run

First, test the detail scraper with a single run to make sure it works:

```bash
# Temporarily set loop_active to 'no' in config
python detail_scraper.py
```

You should see output like:
```
INFO: Starting detail scraper for Storia and Imobiliare.ro
INFO: Found 3 listings to update (filtered from 10 total)
INFO: Fetching details for: Apartament 3 camere...
INFO: Updated fields: description, images, construction_year, floor
...
INFO: Detail scraping complete: 3 updated, 0 failed/skipped
```

### 3. Choose Your Deployment Method

#### Option A: Run Manually (Simplest)

Just run the detail scraper whenever you want:

```bash
python detail_scraper.py
```

Set `loop_active: no` for this mode.

#### Option B: Continuous Loop (Like Main Scraper)

Run as a separate process alongside main scraper:

```bash
# Terminal 1: Main scraper
python flathunt.py

# Terminal 2: Detail scraper
python detail_scraper.py
```

Set `loop_active: yes` for this mode.

#### Option C: Systemd Service (Recommended for Production)

```bash
# 1. Copy and edit service file
sudo cp sample-detail-scraper.service /etc/systemd/system/detail-scraper.service
sudo nano /etc/systemd/system/detail-scraper.service

# 2. Update paths in the service file:
#    - WorkingDirectory=/path/to/your/flathunter
#    - ExecStart=/path/to/your/python detail_scraper.py

# 3. Enable and start
sudo systemctl enable detail-scraper.service
sudo systemctl start detail-scraper.service

# 4. Check status
sudo systemctl status detail-scraper.service
```

#### Option D: Cron Job (Scheduled Runs)

```bash
# Edit crontab
crontab -e

# Add entry (runs every hour)
0 * * * * cd /path/to/flathunter && python detail_scraper.py >> /var/log/detail-scraper.log 2>&1
```

For cron, set `loop_active: no` so it exits after each run.

#### Option E: Docker Compose

Update your `docker-compose.yaml`:

```yaml
services:
  flathunter:
    # ... existing main service ...

  detail-scraper:
    build:
      context: .
      dockerfile: Dockerfile.detail-scraper
    volumes:
      - ./data:/app/data
    environment:
      # Same environment variables as main service
      - FLATHUNTER_TARGET_URLS=${FLATHUNTER_TARGET_URLS}
      - FLATHUNTER_DATABASE_LOCATION=/app/data
```

Then:
```bash
docker-compose up -d detail-scraper
```

## What Changes in Your Database?

The detail scraper adds new fields to existing listings:

**Before detail scraper:**
```json
{
  "id": 12345,
  "title": "Apartament 3 camere Bucuresti",
  "price": "€120,000",
  "size": "75",
  "rooms": "3",
  "url": "https://...",
  "image": "https://.../thumbnail.jpg"
}
```

**After detail scraper:**
```json
{
  "id": 12345,
  "title": "Apartament 3 camere Bucuresti",
  "price": "€120,000",
  "size": "75",
  "rooms": "3",
  "url": "https://...",
  "image": "https://.../thumbnail.jpg",
  "description": "Apartament modern cu 3 camere in zona centrala...",
  "images": ["img1.jpg", "img2.jpg", "img3.jpg", ...],
  "construction_year": "2020",
  "floor": "4",
  "building_type": "Cărămidă",
  "condition": "Nou",
  "heating": "Centrala termică",
  "parking": "Subsol"
}
```

## Adjusting Your Notification Messages

You can now use the new fields in your Telegram messages. Update your message template:

```yaml
message:
  title: |
    {title}
    💰 {price} | 📐 {size} m² | 🚪 {rooms} camere
    
    📝 {description}
    
    🏢 An: {construction_year} | Etaj: {floor}
    🔥 {heating}
    🚗 {parking}
    
    📸 {image_count} imagini disponibile
    🔗 {url}
```

## Troubleshooting Common Issues

### "No listings to update"

**Problem:** Detail scraper finds no listings to process.

**Solution:**
1. Make sure main scraper has run and found listings
2. Check database: `sqlite3 data/processed_ids.db "SELECT COUNT(*) FROM exposes"`
3. Verify you have Storia or Imobiliare.ro URLs configured
4. Increase `hours_lookback` to look further back

### Chrome/WebDriver not found

**Problem:** Error about missing Chrome driver.

**Solution:**
```bash
python chrome_driver_install.py
```

### Rate limiting / Being blocked

**Problem:** Detail scraper gets blocked after a few requests.

**Solutions:**
1. Increase sleep time: `loop: sleeping_time: 1200` (20 minutes)
2. Enable jitter: `loop: random_jitter: True`
3. Reduce lookback: `detail_scraper: hours_lookback: 6`
4. Use proxies: `use_proxy_list: true`
5. Add CAPTCHA solver (Capmonster recommended)

### Detail scraper conflicts with main scraper

**Problem:** Both scrapers seem to interfere with each other.

**Solution:**
- They use the same database but different operations (read vs write)
- They should not conflict
- If issues persist, try running them at different times:
  - Main scraper: Every 10 minutes
  - Detail scraper: Every hour (offset by 30 minutes)

### Old listings not getting updated

**Problem:** Only recent listings get details, old ones don't.

**Solution:**
This is by design (controlled by `hours_lookback`). To update old listings:

```python
# One-time script to update all Storia/Imobiliare.ro listings
from flathunter.config import Config
from flathunter.idmaintainer import IdMaintainer
from detail_scraper import DetailScraper
import datetime

config = Config()
id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')
scraper = DetailScraper(config, id_watch)

# Look back 30 days instead of 24 hours
scraper.scrape_details(hours_ago=30*24)
```

## Performance Considerations

### Memory Usage
- Detail scraper uses ~200-300 MB RAM
- Chrome driver uses ~150-200 MB RAM per instance
- Total: ~400-500 MB RAM

### Disk Space
- Images are stored as URLs, not downloaded
- Database grows by ~2-5 KB per listing with details
- 1000 listings ≈ 2-5 MB additional space

### Network Usage
- Main scraper: ~50-100 KB per listing
- Detail scraper: ~500 KB - 2 MB per listing (depends on images)
- Hourly run with 10 new listings: ~5-20 MB

### Timing
- Detail scraper: ~5-10 seconds per listing
- With 600 second sleep time:
  - Can process ~6 listings per hour
  - 24 hours lookback with 50 new listings: ~8 hours total

Adjust `sleeping_time` based on your needs:
- Fast updates (more risk): 300 seconds (5 min)
- Balanced: 600 seconds (10 min)
- Safe: 1200 seconds (20 min)

## Monitoring

### Check Logs

```bash
# Systemd service
journalctl -u detail-scraper.service -f

# Manual run
python detail_scraper.py 2>&1 | tee detail-scraper.log

# Docker
docker logs -f detail-scraper
```

### Check Database

```bash
sqlite3 data/processed_ids.db "
  SELECT crawler, COUNT(*) as count, 
         SUM(CASE WHEN details LIKE '%description%' THEN 1 ELSE 0 END) as with_details
  FROM exposes 
  GROUP BY crawler
"
```

### Verify Updates

```python
from flathunter.idmaintainer import IdMaintainer
from flathunter.config import Config

config = Config()
id_watch = IdMaintainer(f'{config.database_location()}/processed_ids.db')

# Get recent Storia/Imobiliare.ro listings
exposes = id_watch.get_exposes_since(datetime.datetime.now() - datetime.timedelta(hours=24))

storia_imob = [e for e in exposes if e.get('crawler') in ['Storia', 'ImobiliareRo']]
with_details = [e for e in storia_imob if 'description' in e]

print(f"Storia/Imobiliare.ro listings: {len(storia_imob)}")
print(f"With details: {len(with_details)}")
print(f"Coverage: {len(with_details)/len(storia_imob)*100:.1f}%")
```

## Rollback

If you want to disable the detail scraper:

1. Stop the service:
   ```bash
   sudo systemctl stop detail-scraper.service
   sudo systemctl disable detail-scraper.service
   ```

2. Remove from cron:
   ```bash
   crontab -e  # Remove the detail-scraper line
   ```

3. Remove from config:
   ```yaml
   # Just comment out or remove the detail_scraper section
   ```

Existing detailed data will remain in the database but won't be updated.

## Next Steps

- Read the [full documentation](DETAIL_SCRAPER.md)
- Check [performance tips](DETAIL_SCRAPER.md#performance-considerations)
- See [example usage](../examples/detail_scraper_example.py)
- Deploy to [Google Cloud](DETAIL_SCRAPER.md#google-cloud-deployment)

## Support

- Check logs for specific error messages
- Review [troubleshooting section](DETAIL_SCRAPER.md#troubleshooting)
- Open an issue on GitHub with logs and config (remove sensitive data)
