---
name: webapi_crawler_analyzer
description: A skill for capturing web requests and responses with event injection for natural language instructions, leaving analysis to LLM. Supports dynamic content handling and browser automation for API discovery.
---

# WebAPI Crawler Analyzer Skill

This skill captures web requests and responses using natural language instructions with event injection capabilities. The skill leverages browser automation to interact with web pages and returns raw data for LLM-powered analysis and interpretation.

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
- Capture network traffic from web pages using natural language instructions
- Interact with dynamic content (fill forms, click buttons, etc.)
- Discover API endpoints by monitoring network requests
- Extract data from JavaScript-heavy websites
- Perform automated browser interactions based on natural language
- Collect raw request/response data for custom analysis

## Function Interface

The skill provides a function that can be called by an LLM:

```python
def webapi_crawler_analyzer_skill(
    instructions: str
) -> Dict[str, Any]:
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instructions` | string | Yes | Natural language instructions including URL and actions (e.g., "Open https://example.com, enter 'phone' in search box, click search button") |

## Processing Flow

### Phase 1: Page Loading and Interaction
1. **URL Extraction**: Extract target URL from user instructions
2. **Browser Initialization**:
   - Launch Playwright headless browser with anti-detection measures
   - Configure user agent and HTTP headers to appear as a real user
3. **Interaction Operations**:
   - Execute operations based on natural language instructions
   - Monitor network requests during page load and interactions
4. **Request Capture**:
   - Intercept all network requests and responses
   - Filter out static resources (images, stylesheets, fonts)
   - Store raw request/response data for LLM analysis

### Phase 2: Data Collection
1. **Network Traffic Capture**:
   - Collect all XHR/Fetch, document, and script requests
   - Store URLs, methods, headers, and response content
2. **HTML Content Capture**:
   - Retrieve final page HTML after interactions
   - Capture DOM state after JavaScript execution
3. **Return Raw Data**:
   - Provide collected data to LLM for custom analysis

## Output Format

The skill returns a JSON object with the following structure:

```json
{
  "execution_summary": "Captured 15 network requests and HTML content",
  "raw_requests_data": [
    {
      "url": "https://api.example.com/search",
      "method": "GET",
      "resource_type": "xhr",
      "response": "{ \"results\": [...] }",
      "headers": {
        "content-type": "application/json"
      },
      "status": 200
    }
  ],
  "html_content": "<html>...</html>",
  "instructions_used": "Open https://example.com, enter 'search term' in search box, click search button"
}
```

## Working Principles

### Browser Automation
- **Stealth Mode**: Implements anti-detection measures to avoid bot blocking
- **Event Injection**: Translates natural language to browser interactions
- **Resource Filtering**: Focuses on meaningful requests (XHR, API calls) while filtering static resources

### Natural Language Processing
- **Instruction Parsing**: Extracts URLs and interaction commands from natural language
- **Action Mapping**: Maps human instructions to specific browser operations
- **Flexible Input**: Accepts varied instruction formats and terminology

### Data Capture
- **Complete Logging**: Captures all network traffic during the session
- **Response Storage**: Stores response bodies for later analysis
- **Metadata Preservation**: Maintains headers, status codes, and request types

## Usage Examples

### Example 1: Basic API Discovery
**User Input**:
```
instructions: "Open https://httpbin.org/get, submit any form with test data"
```

**Execution Process**:
1. Load page at https://httpbin.org/get
2. Look for forms and submit with test data
3. Capture all network requests made during the process
4. Return raw request/response data for analysis

**Output Summary**:
```json
{
  "execution_summary": "Captured 2 network requests and HTML content",
  "raw_requests_data": [
    {
      "url": "https://httpbin.org/get",
      "method": "GET",
      "resource_type": "document",
      "response": "{ ... }",
      "status": 200
    }
  ],
  "html_content": "<!DOCTYPE html>...",
  "instructions_used": "Open https://httpbin.org/get, submit any form with test data"
}
```

### Example 2: Search Interaction
**User Input**:
```
instructions: "Go to https://example-shop.com, search for 'wireless headphones' and click search"
```

**Execution Process**:
1. Navigate to https://example-shop.com
2. Find search input field and enter "wireless headphones"
3. Click search button
4. Capture all API requests triggered by the search
5. Return raw data for LLM to analyze and extract relevant information

## Limitations and Considerations

1. **Rate Limiting**: Be mindful of website rate limits when making repeated requests
2. **Anti-Bot Measures**: Some sites may still detect and block automated access despite stealth measures
3. **Resource Intensive**: Browser automation consumes more resources than direct API calls
4. **Timeouts**: Complex pages may require longer timeouts for full loading
5. **Analysis Responsibility**: The LLM is responsible for analyzing the raw data returned by this skill

> **Tip**: Use this skill when you need to understand the network behavior of a website or when traditional API discovery methods are insufficient. The raw data returned can be processed by your LLM to extract specific information based on your needs.