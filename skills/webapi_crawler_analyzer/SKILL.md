---
name: webapi_crawler_analyzer
description: A skill for intelligently identifying crawlable WebAPI endpoints from web pages using natural language instructions. Supports dynamic content handling, pagination scenarios, and falls back to HTML parsing when APIs aren't found. Prioritizes XHR requests and uses LLM assistance to identify data sources that best match user requirements.
---

# WebAPI Crawler Analyzer Skill

This skill intelligently identifies crawlable WebAPI endpoints from web pages using natural language instructions. It supports dynamic content handling, pagination scenarios, and falls back to HTML parsing when APIs aren't found. The skill prioritizes XHR requests and uses LLM assistance to identify data sources that best match user requirements.

## Environment Configuration

Before using this skill, you need to configure the Python environment:

1. Check if a Python virtual environment exists in the `assets` directory (`assets/.venv`).
2. If the virtual environment does not exist, follow the setup instructions in [SETUP.md](./SETUP.md) to create one:
   - Create a virtual environment using `uv venv`
   - Install dependencies with `uv pip install -r requirements.txt`
   - Install Playwright browsers with `python -m playwright install chromium`
3. If the virtual environment exists in `assets/.venv`, activate it before running any Python commands:
   ```bash
   source assets/.venv/bin/activate
   ```

## When to Use This Skill

Use this skill when you need to:
- Discover API endpoints from web pages using natural language instructions
- Extract structured data from websites with complex JavaScript interactions
- Analyze network requests to identify data sources that match your description
- Handle pagination scenarios intelligently
- Perform fallback HTML parsing when no APIs are found
- Interact with dynamic content (fill forms, click buttons, etc.)

## Function Interface

The skill provides a function that can be called by an LLM:

```python
def webapi_crawler_analyzer_skill(
    instructions: str,
    data_description: str,
    max_depth: int = 1,
    confirm_each_depth: bool = True,
    include_pagination: bool = False
) -> Dict[str, Any]:
```

## Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `instructions` | string | Yes | - | Natural language instructions including URL and actions (e.g., "Open https://example.com, enter 'phone' in search box, click search button") |
| `data_description` | string | Yes | - | Description of the data you want to extract (e.g., "product names, prices, inventory status") |
| `max_depth` | integer | No | 1 | Maximum crawling depth (0 means only current page) |
| `confirm_each_depth` | boolean | No | true | Whether to confirm before proceeding to next depth level |
| `include_pagination` | boolean | No | false | Whether to treat pagination links as next level (default: false) |

## Processing Flow

### Phase 1: Page Loading and Interaction
1. **URL Extraction**: Extract target URL from user instructions
2. **Interaction Operations**:
   - Launch Playwright headless browser
   - Send page screenshot/HTML summary and user instructions to LLM in thinking mode
   - LLM generates specific operation steps (e.g., `page.fill('#search-box', 'playwright')`, `page.click('button.execute')`)
   - Execute operations and wait for network requests to complete
3. **Request Capture**:
   - Intercept all network requests and responses
   - Categorize by type: Document > XHR/Fetch > Script > Other

### Phase 2: API Intelligent Analysis
1. **Preliminary Filtering**:
   - Prioritize XHR/Fetch type requests
   - Keep only successful responses (200-299) with JSON/text Content-Type
2. **LLM-Assisted Matching** (Two-stage):
   - **Stage 1**: LLM generates grep-like search commands to filter N candidate APIs
   - **Stage 2**: LLM analyzes each candidate API, evaluating match with `data_description`
     - Field name matching (e.g., "price" vs "商品价格")
     - Data structure standardization (JSON > text > HTML)
     - Data volume sufficiency (list vs single record)
3. **Pagination Special Handling**:
   - Detect URL patterns: `?page=`, `?p=`, `/page/number`
   - Identify pagination APIs: containing `pagination`, `total_pages` fields
   - Default behavior: Don't add pagination links to next level, analyze pagination API itself

### Phase 3: Data Extraction Strategy
1. **Primary Solution**: Directly use matching WebAPI (with full URL and parameters)
2. **Fallback Solution** (when no API):
   - Use BeautifulSoup to parse HTML
   - LLM generates CSS selectors or XPath paths
3. **Depth Crawling Control**:
   - When `max_depth > 0`, extract links from page
   - Exclude: pagination links, external domains, already visited URLs
   - Pause at depth limit, wait for user confirmation

## Output Format

The skill returns a JSON object with the following structure:

```json
{
  "execution_summary": "Successfully executed 2 interaction steps, captured 15 network requests",
  "recommended_apis": [
    {
      "url": "https://api.example.com/search",
      "method": "POST",
      "priority_score": 0.95,
      "matched_fields": ["name", "price", "stock_status"],
      "sample_data": [{"name": "Product A", "price": 199, "...": "..."}],
      "direct_use_example": "curl -X POST https://api.example.com/search -d '{\"query\":\"playwright\"}'"
    }
  ],
  "fallback_html_selectors": {
    "if_no_api": [
      {"element": "Product Name", "selector": ".product-title", "example": "<div class='product-title'>Smart Watch</div>"},
      {"element": "Price", "selector": ".price-value", "example": "<span class='price-value'>¥299</span>"}
    ]
  },
  "next_actions": {
    "requires_confirmation": true,
    "available_depth_links": [
      {"url": "https://example.com/product/123", "context": "Product Detail Page"},
      {"url": "https://example.com/product/456", "context": "Product Detail Page"}
    ],
    "pagination_api_detected": "https://api.example.com/products?page=2"
  }
}
```

## Working Principles

### Intelligent Request Analysis
- **Priority Queue**: Document > XHR > Script > Other, breaking the conventional pattern of starting from HTML
- **Semantic Matching**: Not relying on simple keywords, but understanding data structure and context
- **Pagination Optimization**: Treating pagination as different requests to the same data source, not new pages

### Interaction Operation Mechanism
1. LLM converts natural language instructions to Playwright operation sequences:
   ```
   User instruction: "Enter 'playwright' in search box, click execute button"
   ↓
   LLM generates operations:
   1. page.wait_for_selector('#search-box')
   2. page.fill('#search-box', 'playwright')
   3. page.click('button:has-text("execute")')
   4. page.wait_for_load_state('networkidle')
   ```

### No-API Fallback Strategy
When no suitable API is found:
1. LLM analyzes HTML structure, identifying data containers
2. Generates targeted CSS selectors
3. Provides example code:
   ```python
   from bs4 import BeautifulSoup
   soup = BeautifulSoup(html_content, 'html.parser')
   items = soup.select('div.skill-item')
   for item in items:
       name = item.select_one('.skill-name').text.strip()
       # ... other field extraction
   ```

## Usage Examples

### Example 1: API Discovery with Interaction
**User Input**:
```
instructions: "Open https://skillsmp.com/zh/search, enter 'playwright' in search box, click execute button"
data_description: "Skill name, author, download count"
max_depth: 0
```

**Execution Process**:
1. Load page, execute search operation
2. Capture XHR request: `https://api.skillsmp.com/search?q=playwright`
3. LLM analyzes response, confirms containing required fields
4. Skip depth crawling (max_depth=0)

**Output Summary**:
```json
{
  "recommended_apis": [{
    "url": "https://api.skillsmp.com/search",
    "matched_fields": ["skill_name", "author", "downloads"],
    "direct_use_example": "curl 'https://api.skillsmp.com/search?q=playwright'"
  }]
}
```

### Example 2: Pagination Scenario Handling
**User Input**:
```
instructions: "Visit https://example-commerce.com/products"
data_description: "Names and prices of all products"
max_depth: 1,
include_pagination: false
```

**Execution Process**:
1. Analyze XHR requests, discover `/api/products?page=1` containing product data
2. Detect pagination parameters, automatically analyze total pages
3. Don't add pagination links to next level, instead provide complete crawling solution:
   ```
   for page in range(1, total_pages+1):
       response = requests.get(f"/api/products?page={page}")
   ```

### Example 3: HTML Parsing When No API
**User Input**:
```
instructions: "Open https://legacy-website.com/listings"
data_description: "Contact phone and address"
```

**Execution Process**:
1. No matching XHR/API requests found
2. LLM analyzes HTML structure, generates CSS selectors
3. Extract key element positions

**Output Summary**:
```json
{
  "fallback_html_selectors": {
    "if_no_api": [
      {"element": "Phone", "selector": ".contact-info .phone"},
      {"element": "Address", "selector": ".contact-info .address"}
    ]
  },
  "extraction_code_template": "soup.select('.listing-item') → iterate to extract"
}
```

## Limitations and Considerations

1. **Dynamic Content Limitations**: Highly JavaScript-rendered pages may require custom interaction scripts
2. **Anti-Crawling Mechanisms**: Does not handle CAPTCHAs, IP blocking, or other anti-crawling measures
3. **Data Volume Control**: Single analysis processes at most 50 candidate APIs to avoid LLM overload
4. **Privacy Compliance**: Automatically skips requests containing sensitive paths like `/auth/`, `/login/`
5. **Performance Boundaries**: Single page analysis timeout = 30 seconds, depth crawling recommended in batches

> **Tip**: For complex websites, first use `max_depth=0` to analyze current page APIs, then decide whether to crawl deeper. For pagination scenarios, it's recommended to directly use the detected pagination API rather than clicking through pages.