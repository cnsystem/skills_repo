# WebAPI Crawler Analyzer Skill - Setup Instructions

## Setup

To use this skill, you need to set up the virtual environment:

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

## Requirements

- Python 3.7+
- Playwright library
- BeautifulSoup4 for HTML parsing fallback
- Network access to target websites