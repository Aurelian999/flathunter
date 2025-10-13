# Flathunter AI Coding Instructions

## Architecture Overview

Flathunter is a **web scraping bot for real estate listings** that uses a **plugin-based crawler architecture** with **processor chain pattern**. Key components:

- **Entry points**: `flathunt.py` (CLI loop) and `main.py` (web interface)
- **Core flow**: `Hunter` → `Crawler`s → `ProcessorChain` → `Notifier`s
- **Data stores**: SQLite locally, Google Cloud Firestore for cloud deployment
- **Crawlers**: Site-specific implementations in `flathunter/crawler/` (ImmoScout24, Immowelt, WG-Gesucht, etc.)
- **Notifiers**: Telegram, Slack, Mattermost, Apprise in `flathunter/notifiers/`

## Configuration Pattern

**Environment-first configuration** with YAML fallback:
- Environment variables prefixed with `FLATHUNTER_` (see `Env` class in `config.py`)
- YAML config loads from `config.yaml` (template: `config.yaml.dist`)
- Config validation happens in crawler `__init__` methods
- Use `StringConfig` in tests for inline YAML

## Crawler Development

**All crawlers inherit from `abstract_crawler.Crawler`**:
- Must implement `extract_data(soup)` method
- Define `URL_PATTERN` class variable for URL matching
- Handle bot detection via headless Chrome with `get_soup_from_url(..., driver=driver)`
- Support captcha solving (reCAPTCHA, GeeTest, AWS WAF) via configured solvers
- Use backoff decorators for retry logic on network/captcha failures

**Example crawler structure**:
```python
class NewSite(Crawler):
    URL_PATTERN = re.compile(r'https://newsite\.com')
    
    def extract_data(self, soup):
        # Return list of expose dicts with keys: id, title, price, size, rooms, url
        pass
```

## Processor Chain Pattern

**ProcessorChainBuilder** creates functional pipelines:
- `crawl_for_exposes()` → `apply_filter()` → `resolve_addresses()` → `calculate_durations()` → `send_messages()`
- Each processor is a generator that yields modified exposes
- Built via `ProcessorChain.builder(config).operation().build()`
- Custom processors extend `abstract_processor.Processor`

## Testing Approach

**Use pytest with mocked dependencies**:
- Test crawlers with `DummyCrawler` and static HTML fixtures in `test/crawler/fixtures/`
- Test filters with `StringConfig` and controlled expose data
- Mock external APIs (Google Maps, Telegram) in unit tests
- Integration tests use environment variables for real API keys

## Development Commands

```bash
# Setup
pipenv install && pipenv shell

# Testing
pytest                           # All tests
coverage run                     # With coverage
pytest test/test_hunter.py      # Specific test

# Local development
python config_wizard.py         # Generate config
python flathunt.py              # Run CLI bot
python main.py                  # Run web interface

# Docker deployment
docker-compose up               # With docker-compose.yaml
```

## Cloud Deployment Patterns

**Google Cloud support** via dual entry points:
- `main.py`: App Engine web interface (uses GoogleCloudIdMaintainer)
- `cloud_job.py`: Cloud Run job for scheduled crawling
- Environment variable configuration takes precedence
- Firestore replaces SQLite for processed IDs tracking
- Use `WDM_LOCAL=1` for cached WebDriver manager

## Bot Detection Handling

**Multi-layered approach**:
- Proxy rotation via `use_proxy_list: true`
- Headless Chrome with `undetected-chromedriver`
- Captcha solving services (prefer Capmonster for ImmoScout24)
- Cookie injection for ImmoScout24: `immoscout_cookie` config
- Request throttling with `random_jitter` and configurable intervals

When adding new crawlers, **always test bot detection** and implement appropriate countermeasures.