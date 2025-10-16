# Storia.ro Bot Detection Fix - Summary

## Changes Made

### 1. Config Updates (`config.yaml`)

#### Enabled Proxy Support
```yaml
use_proxy_list: True
```

#### Configured CAPTCHA Solver
```yaml
captcha:
  capmonster:
    api_key: YOUR_API_KEY_HERE
```

### 2. Enhanced Storia Crawler (`flathunter/crawler/storia.py`)

#### Added Random Delays
- Changed from fixed 2-second waits to random 2-4 second delays
- Added random jitter to scroll timing (0.5-2 seconds)

#### Human-like Scrolling Behavior
- Progressive scrolling: 25% → 50% → 75% → 100% → 80%
- Random delays between each scroll action
- Mimics human browsing patterns

#### CAPTCHA Detection
- Detects 'captcha-delivery.com' in page source
- Detects 'please enable js' messages
- Logs helpful error messages with solutions
- Returns empty soup to avoid processing error pages

#### Error Messages
When CAPTCHA is detected, logs:
```
[ERROR] Storia.ro: CAPTCHA/bot detection triggered!
[INFO] Possible solutions:
  1. Enable 'use_proxy_list: True' in config.yaml
  2. Configure a CAPTCHA solver (Capmonster recommended)
  3. Increase 'sleeping_time' in config.yaml
  4. Wait a few hours before retrying
```

### 3. Documentation

Created comprehensive guides:
- `docs/STORIA_BOT_DETECTION.md` - Full troubleshooting guide
- `proxies.txt.example` - Proxy configuration template

## Quick Start After Bot Detection

### Immediate Actions (Choose One or More)

**Option A: Wait & Increase Interval** (Free, slowest)
1. Stop Flathunter
2. Wait 2-4 hours
3. Increase `sleeping_time` to 1800 (30 minutes)
4. Restart

**Option B: Enable Proxies** (Low cost, fast)
1. Get proxy list from free-proxy-list.net
2. Create `proxies.txt` with proxy addresses
3. Config already has `use_proxy_list: True`
4. Restart

**Option C: CAPTCHA Solver** (Moderate cost, most reliable)
1. Register at https://capmonster.cloud/
2. Deposit $5-10
3. Add API key to `captcha.capmonster.api_key` in config
4. Restart

**Option D: All Three** (Best reliability)
- Combine increased interval + proxies + CAPTCHA solver
- Most expensive but most reliable
- Recommended for 24/7 operation

## Testing

Run the test script to verify functionality:
```bash
python test_storia_page.py
```

Expected output:
```
✅ SUCCESS: Page loaded with content
📊 Extracted 40 listings
📝 First listing sample: ...
```

If CAPTCHA detected:
```
❌ ERROR: Page is too short (possible bot detection)
```

## Cost Estimates

### Capmonster CAPTCHA Solving
- $0.60-1.00 per 1000 CAPTCHAs
- 30-minute intervals ≈ 48 requests/day
- Monthly cost: ~$1-2 (assuming 50% CAPTCHA rate)

### Proxy Services
- **Free**: $0 but unreliable, may be blacklisted
- **Datacenter**: $5-20/month for basic rotation
- **Residential**: $50-100/month for premium IPs

### Total Monthly Cost (30min intervals)
- **Minimal**: $0 (long intervals only)
- **Standard**: $10-25 (free proxies + CAPTCHA)
- **Premium**: $60-120 (residential proxies + CAPTCHA)

## Monitoring

Watch logs for these indicators:

### Healthy Crawling
```
[DEBUG] Storia.ro: Retrieved page with 1203842 characters
[DEBUG] Found 40 advertisements on Storia.ro page
[INFO] Sending notification...
```

### Warning Signs
```
[WARNING] Storia.ro returned very short page (500 chars)
```
→ Increase `sleeping_time` immediately

### CAPTCHA Triggered
```
[ERROR] Storia.ro: CAPTCHA/bot detection triggered!
```
→ Stop bot, wait, enable proxies or CAPTCHA solver

## Rollback

If changes cause issues, revert to original:

1. Set `sleeping_time: 600`
2. Remove `use_proxy_list: True`
3. Comment out `captcha` section
4. Restore `flathunter/crawler/storia.py` from git:
   ```bash
   git checkout flathunter/crawler/storia.py
   ```

## Next Steps

1. **Stop your current Flathunter** (Ctrl+C)
2. **Review `config.yaml`** - ensure all changes match your needs
3. **Choose a solution**:
   - Quick fix: Just increase `sleeping_time` to 1800
   - Better: Enable proxies (requires proxy list)
   - Best: Enable proxies + CAPTCHA solver
4. **Restart Flathunter**:
   ```bash
   python flathunt.py
   ```
5. **Monitor first hour** - check logs for CAPTCHA warnings
6. **Adjust as needed** - increase interval if still seeing issues

## Support

If issues persist after trying all solutions:
1. Check `docs/STORIA_BOT_DETECTION.md` for detailed troubleshooting
2. Run `test_storia_page.py` to diagnose
3. Open GitHub issue with logs

## Files Modified

- ✅ `config.yaml` - Increased interval, enabled proxies, added CAPTCHA config
- ✅ `flathunter/crawler/storia.py` - Enhanced bot detection handling
- ✅ `docs/STORIA_BOT_DETECTION.md` - Created troubleshooting guide
- ✅ `proxies.txt.example` - Created proxy template
- ✅ `docs/STORIA_FIX_SUMMARY.md` - This file
