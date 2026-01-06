---
name: webapi_crawler_analyzer
description: A skill for intelligently identifying crawlable WebAPI endpoints from web pages and handling multi-level page crawling with depth control. Use this skill when you need to discover APIs from web pages, analyze network requests, or extract structured data from websites with complex JavaScript interactions.
---

# WebAPI Crawler Analyzer Skill

This skill focuses on intelligently identifying crawlable WebAPI endpoints from web pages and handling multi-level page crawling with depth control. It uses Playwright to capture network requests and analyzes them by priority to find the most relevant APIs for the requested data.

## When to Use This Skill

Use this skill when you need to:
- Discover API endpoints from a given webpage
- Extract structured data from websites with complex JavaScript interactions
- Analyze network requests to identify data sources
- Perform multi-level crawling with controlled depth
- Identify APIs that provide specific data types (e.g., product prices, inventory, user data)

## Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | - | Starting URL for the crawl |
| `data_description` | string | Yes | - | Description of the data you want to extract (e.g., "product names, prices, inventory") |
| `max_depth` | integer | No | 1 | Maximum crawling depth to prevent infinite loops |
| `confirm_each_depth` | boolean | No | true | Whether to confirm before proceeding to next depth level |

## Output Format

The skill returns a JSON object with the following structure:

```json
{
  "analyzed_apis": [
    {
      "url": "https://api.example.com/data",
      "method": "GET/POST",
      "content_type": "application/json",
      "matched_keywords": ["price", "stock"],
      "priority_level": 1,
      "sample_response": "{...}"
    }
  ],
  "next_depth_links": [
    "https://example.com/product1",
    "https://example.com/product2"
  ],
  "requires_user_confirmation": true,
  "analysis_summary": "Summary of the analysis performed"
}
```

## Core Execution Logic

### 1. Network Request Capture (Playwright)

The skill uses Playwright to launch a headless browser and capture all network requests made during page load:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Intercept all requests
    requests = []
    page.on("requestfinished", lambda req: requests.append({
        "url": req.url,
        "method": req.method,
        "resource_type": req.resource_type,
        "response": req.response().text() if req.response() else None,
        "headers": req.headers
    }))

    page.goto(input_url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)  # Allow dynamic content to load
    browser.close()
```

### 2. API Priority Analysis

APIs are analyzed in priority order, with the most likely data sources checked first:

| Priority | Request Type | Matching Logic |
|----------|--------------|----------------|
| 1 | Document (HTML) | Check for embedded JSON in `<script>` tags (e.g., `__NEXT_DATA__`) |
| 2 | XHR/Fetch | Filter for `content-type: application/json`, check for matching keywords |
| 3 | JS Dynamic Injection | Parse JS files for stringified JSON |
| 4 | Other Text Types | Process `text/plain`/`application/text` with regex for structured data |

### 3. Breadth-First Crawling

- Initial depth = 0 (starting page)
- Each level increases depth: `current_depth += 1`
- Stops when `current_depth >= max_depth`
- Uses Bloom Filter to avoid duplicate URLs
- Skips non-same-origin links

### 4. Safety and Performance

- Timeout: 15 seconds per page (configurable)
- Rate limiting: Max 5 requests per second
- Automatic data sanitization for sensitive fields
- Proper resource cleanup

## Advanced Features

### Interaction Scripts
For pages requiring user interaction to load data, you can provide custom scripts:

```javascript
// Example interaction script to click a "Load More" button
await page.click('#load-more');
await page.waitForTimeout(1000);
```

### Authentication Support
Support for authenticated endpoints via headers:

```json
{
  "auth_headers": {
    "Authorization": "Bearer your-token",
    "X-API-Key": "your-api-key"
  }
}
```

## Usage Examples

### Basic Usage
```json
{
  "url": "https://example-commerce.com/products",
  "data_description": "product names, prices, inventory status"
}
```

### With Depth Control
```json
{
  "url": "https://example-commerce.com/products",
  "data_description": "product names, prices, inventory status",
  "max_depth": 2,
  "confirm_each_depth": true
}
```

### With Authentication
```json
{
  "url": "https://api.example.com/data",
  "data_description": "user profiles, permissions",
  "auth_headers": {
    "Authorization": "Bearer token123"
  }
}
```

## Best Practices

1. **Be Specific with Data Description**: The more specific you are about the data you want, the better the matching will be.

2. **Control Depth Appropriately**: Use `max_depth` carefully to avoid unintended crawling of entire sites.

3. **Use Confirmations**: For sensitive or important crawling tasks, keep `confirm_each_depth` as true.

4. **Handle Dynamic Content**: For SPAs or heavily JavaScript-dependent sites, consider using interaction scripts.

5. **Respect Rate Limits**: The skill includes rate limiting, but be mindful of the target site's policies.

## Troubleshooting

### Common Issues

- **No APIs Found**: The site might be a static HTML site with no dynamic API calls
- **Timeout Errors**: The page might be slow to load or have complex JavaScript
- **Authentication Required**: The data might be behind a login wall
- **Rate Limited**: The site might have anti-bot measures in place

### Solutions

- For static sites, look for embedded JSON in the HTML source
- For timeout issues, try increasing the timeout in the skill configuration
- For authentication issues, provide appropriate headers
- For rate limiting, reduce the crawling speed or add delays