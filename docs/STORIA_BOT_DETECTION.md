# Storia.ro Bot Detection & CAPTCHA Troubleshooting

## Problem

You're seeing errors like:
```
Got response (403): b'<html lang="en"><head><title>immowelt.de</title>...
Please enable JS and disable any ad blocker...
captcha-delivery.com...
```

This means Storia.ro has detected automated scraping and triggered CAPTCHA protection.

## Solutions (Try in Order)

### 1. **Immediate: Increase Crawling Interval**

Storia.ro rate-limits based on request frequency. Edit `config.yaml`:

```yaml
loop:
  active: yes
  sleeping_time: 1800  # 30 minutes between crawls
  random_jitter: true
```

**Recommended intervals:**
- Light usage: 900 seconds (15 minutes)
- Medium usage: 1800 seconds (30 minutes)
- After CAPTCHA trigger: 3600 seconds (60 minutes)

### 2. **Enable Proxy Rotation**

Rotate IP addresses to avoid rate limiting. Edit `config.yaml`:

```yaml
use_proxy_list: True
```

Then create a file `proxies.txt` in the root directory with proxy addresses:

```
http://username:password@proxy1.example.com:8080
http://username:password@proxy2.example.com:8080
socks5://proxy3.example.com:1080
```

**Free proxy sources:**
- https://free-proxy-list.net/
- https://www.proxy-list.download/
- https://geonode.com/free-proxy-list

**Paid proxy services (more reliable):**
- Bright Data (luminati.io)
- Smartproxy
- Oxylabs

### 3. **Configure CAPTCHA Solver**

Storia.ro uses the same CAPTCHA system as Immowelt. Register for a CAPTCHA solving service:

#### Capmonster (Recommended)

1. Register at https://capmonster.cloud/
2. Deposit funds (~$5 minimum)
3. Get your API key from dashboard
4. Edit `config.yaml`:

```yaml
captcha:
  capmonster:
    api_key: YOUR_API_KEY_HERE
```

**Cost:** ~$0.60-1.00 per 1000 CAPTCHAs

#### 2Captcha (Alternative)

1. Register at https://2captcha.com/
2. Deposit funds
3. Get API key
4. Edit `config.yaml`:

```yaml
captcha:
  2captcha:
    api_key: YOUR_API_KEY_HERE
```

**Cost:** ~$1.00-2.99 per 1000 CAPTCHAs

### 4. **Human-like Behavior (Already Implemented)**

The Storia crawler now includes:
- ✅ Random delays between actions (2-4 seconds)
- ✅ Progressive scrolling (25%, 50%, 75%, 100%, back to 80%)
- ✅ Random scroll timing variations
- ✅ CAPTCHA detection with helpful error messages

### 5. **Temporary: Wait & Retry**

If CAPTCHA is triggered:
1. **Stop the bot** immediately
2. **Wait 2-4 hours** (or overnight)
3. **Increase `sleeping_time`** before restarting
4. Consider enabling proxies

Your IP might have a temporary ban that will expire.

### 6. **Advanced: Residential Proxies**

If datacenter proxies fail, use residential proxies:

```yaml
use_proxy_list: True
```

With `proxies.txt`:
```
http://user:pass@residential-proxy.provider.com:12345
```

Residential IPs are harder to detect as they come from real ISP networks.

## Monitoring & Prevention

### Check Logs for CAPTCHA Detection

The crawler now logs CAPTCHA triggers:
```
[ERROR] Storia.ro: CAPTCHA/bot detection triggered!
[INFO] Possible solutions:
  1. Enable 'use_proxy_list: True' in config.yaml
  2. Configure a CAPTCHA solver (Capmonster recommended)
  3. Increase 'sleeping_time' in config.yaml
  4. Wait a few hours before retrying
```

### Best Practices

1. **Start conservative**: Begin with 30-minute intervals
2. **Monitor logs**: Watch for short pages (<1000 chars)
3. **Reduce frequency**: If warnings appear, increase `sleeping_time`
4. **Use proxies early**: Don't wait for CAPTCHA to trigger
5. **Budget for solvers**: If scraping frequently, CAPTCHA costs are inevitable

### Cost Estimates

**Monthly cost for 24/7 Storia.ro scraping:**

| Interval | Requests/day | CAPTCHA/month | Capmonster Cost |
|----------|--------------|---------------|-----------------|
| 15 min   | 96           | ~2,880        | $1.73 - $2.88   |
| 30 min   | 48           | ~1,440        | $0.86 - $1.44   |
| 60 min   | 24           | ~720          | $0.43 - $0.72   |

*Assumes 50% CAPTCHA rate during busy hours*

## Testing After Changes

1. Update `config.yaml` with your changes
2. Restart Flathunter:
   ```bash
   python flathunt.py
   ```
3. Monitor the first few crawl cycles
4. Check Telegram for successful notifications
5. Review logs for CAPTCHA warnings

## Emergency: Reset Your IP

If completely blocked:

### Option A: Home Network
1. Restart your router (may get new IP from ISP)
2. Wait 15-30 minutes
3. Restart Flathunter with higher `sleeping_time`

### Option B: VPN
1. Enable VPN with different country
2. Clear browser cookies
3. Restart Flathunter

### Option C: Proxy Service
1. Use commercial proxy service
2. Configure `proxies.txt`
3. Enable `use_proxy_list: True`

## Still Having Issues?

1. Check Storia.ro in regular browser - is CAPTCHA shown?
2. Verify Chrome/Chromium version matches chromedriver
3. Try disabling headless mode temporarily:
   ```yaml
   captcha:
     driver_arguments:
       # Remove --headless to see what Chrome sees
   ```
4. Check if Storia.ro changed their HTML structure (run `test_storia_page.py`)

## Support

- GitHub Issues: https://github.com/flathunter/flathunter/issues
- Tag issues with `[Storia.ro]` or `[bot-detection]`
