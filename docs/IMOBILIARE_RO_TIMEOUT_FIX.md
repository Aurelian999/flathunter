# Imobiliare.ro Bot Detection & Timeout Troubleshooting

## Problem

You're getting timeouts when trying to scrape Imobiliare.ro. The crawler was waiting up to 300 seconds (5 minutes) for page elements to load.

## Solutions Applied

### 1. **Reduced Timeout** (`flathunter/crawler/imobiliare_ro.py`)

**Before:** `WebDriverWait(driver, 300)` - 5 minutes
**After:** `WebDriverWait(driver, 45)` - 45 seconds

### 2. **Enhanced Bot Detection Handling**

Added same improvements as Storia.ro:
- ✅ **Random delays**: 2-4 seconds (was fixed 2s)
- ✅ **Human-like scrolling**: Progressive 25%→50%→75%→100%→80%
- ✅ **CAPTCHA detection**: Auto-detects and logs helpful errors
- ✅ **Better error handling**: Returns empty soup instead of crashing

### 3. **Config Improvements** (`config.yaml`)

#### Fixed URL Configuration
```yaml
urls:
  - https://www.imobiliare.ro/vanzare-apartamente/judetul-cluj/cluj-napoca?price=130000-200000
```

#### Increased Crawling Interval
```yaml
loop:
  sleeping_time: 900  # Increased from 600 to 900 seconds (15 minutes)
```

#### Enabled Proxy Support
```yaml
use_proxy_list: True
```

## Testing

Run the test script to verify functionality:
```bash
python test_imobiliare_page.py
```

Expected output:
```
✅ SUCCESS: Page loaded with content
📊 Extracted X listings
📝 First listing sample: ...
```

If CAPTCHA detected:
```
❌ ERROR: CAPTCHA/bot detection triggered!
```

## Troubleshooting

### If Still Timing Out

1. **Check Page Structure**: Imobiliare.ro may have changed their HTML
2. **Try Different Selectors**: The current selectors might be outdated
3. **Enable Proxies**: Create `proxies.txt` with proxy addresses
4. **Increase Timeout**: Temporarily increase to 60-90 seconds if needed

### Alternative Selectors to Try

If the current selectors don't work, try these in `extract_data()`:

```python
# Alternative selectors for Imobiliare.ro
advertisements = soup_res.find_all("article")  # Articles instead of divs
advertisements = soup_res.find_all("div", class_=re.compile(r"card|item"))  # Generic cards
advertisements = soup_res.find_all("div", attrs={"data-id": True})  # Data attributes
```

### Debug Steps

1. **Check if page loads at all**:
   ```python
   # In get_page(), add this after driver.get():
   print(f"Page title: {driver.title}")
   print(f"Current URL: {driver.current_url}")
   ```

2. **Check for CAPTCHA**:
   ```python
   # Look for these in page_source:
   if 'captcha' in page_source.lower():
       print("CAPTCHA detected!")
   ```

3. **Manual inspection**:
   - Open Imobiliare.ro in browser
   - Check if CAPTCHA appears
   - Inspect element to find current listing selectors

## Cost Estimates

**Monthly cost for 24/7 Imobiliare.ro scraping:**

| Interval | Requests/day | CAPTCHA/month | Capmonster Cost |
|----------|--------------|---------------|-----------------|
| 15 min   | 96           | ~2,880        | $1.73 - $2.88   |
| 30 min   | 48           | ~1,440        | $0.86 - $1.44   |

*Assumes 50% CAPTCHA rate during busy hours*

## Files Modified

- ✅ `config.yaml` - Fixed URL config, enabled proxies, increased interval
- ✅ `flathunter/crawler/imobiliare_ro.py` - Reduced timeout, added bot detection handling
- ✅ `test_imobiliare_page.py` - Created test script
- ✅ `docs/IMOBILIARE_RO_TIMEOUT_FIX.md` - This file