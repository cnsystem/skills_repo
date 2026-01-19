#!/usr/bin/env python3
"""
WebAPI Crawler Analyzer - Updated Implementation
A script to intelligently identify crawlable WebAPI endpoints from web pages
using natural language instructions, with support for dynamic content and pagination.
"""

import asyncio
import json
import re
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import nltk  # For keyword extraction
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


@dataclass
class APIEndpoint:
    url: str
    method: str
    priority_score: float
    matched_fields: List[str]
    sample_data: Dict[str, Any]
    direct_use_example: str


class WebAPICrawlerAnalyzer:
    def __init__(self, max_depth: int = 1, confirm_each_depth: bool = True, include_pagination: bool = False):
        self.max_depth = max_depth
        self.confirm_each_depth = confirm_each_depth
        self.include_pagination = include_pagination
        self.crawled_urls = set()
        self.visited_domains = set()

    async def analyze(self, instructions: str, data_description: str) -> Dict[str, Any]:
        """
        Main method to analyze using natural language instructions and find relevant API endpoints
        """
        # Extract URL from instructions
        url = self._extract_url_from_instructions(instructions)

        # Extract keywords from data description
        keywords = self._extract_keywords(data_description)

        # Perform the crawling analysis
        result = await self._crawl_and_analyze_with_instructions(
            url, instructions, keywords, depth=0, data_description=data_description
        )

        return result

    def _extract_url_from_instructions(self, instructions: str) -> str:
        """
        Extract URL from natural language instructions
        """
        # Look for URLs in the instructions
        url_pattern = r'https?://[^\s\'"<>]+'
        urls = re.findall(url_pattern, instructions)
        if urls:
            return urls[0]  # Return the first URL found

        # If no URL found, raise an error
        raise ValueError("No URL found in instructions")

    def _extract_keywords(self, data_description: str) -> List[str]:
        """
        Extract keywords from the data description for matching
        """
        # Simple keyword extraction - in a real implementation,
        # we might use NLP techniques for better accuracy
        keywords = re.findall(r'\b\w+\b', data_description.lower())
        return [kw for kw in keywords if len(kw) > 2]  # Filter out short words

    async def _crawl_and_analyze_with_instructions(
        self, url: str, instructions: str, keywords: List[str], depth: int, data_description: str
    ) -> Dict[str, Any]:
        """
        Crawl and analyze using natural language instructions
        """
        if depth >= self.max_depth or url in self.crawled_urls:
            return {
                "execution_summary": f"Reached max depth ({self.max_depth}) or already crawled",
                "recommended_apis": [],
                "fallback_html_selectors": {"if_no_api": []},
                "next_actions": {
                    "requires_confirmation": False,
                    "available_depth_links": [],
                    "pagination_api_detected": None
                }
            }

        self.crawled_urls.add(url)

        # Capture network requests using Playwright with interactions
        requests_data, html_content = await self._capture_network_requests_with_interaction(
            url, instructions
        )

        # Analyze requests by priority
        recommended_apis, pagination_api = self._analyze_requests_intelligently(
            requests_data, keywords, data_description
        )

        # If no APIs found, generate fallback HTML selectors
        fallback_selectors = {}
        if not recommended_apis:
            fallback_selectors = await self._generate_fallback_selectors(
                html_content, data_description
            )

        # Extract links for next depth level
        next_depth_links = self._extract_links_for_next_depth(
            requests_data, url, include_pagination=self.include_pagination
        )

        # Check if we need user confirmation for next depth
        requires_confirmation = (
            self.confirm_each_depth
            and depth + 1 < self.max_depth
            and next_depth_links
        )

        # Prepare execution summary
        execution_summary = f"Successfully executed interaction steps, captured {len(requests_data)} network requests"

        result = {
            "execution_summary": execution_summary,
            "recommended_apis": [self._api_to_dict(api) for api in recommended_apis],
            "fallback_html_selectors": fallback_selectors,
            "next_actions": {
                "requires_confirmation": requires_confirmation,
                "available_depth_links": next_depth_links[:10],  # Limit to first 10 for display
                "pagination_api_detected": pagination_api
            }
        }

        return result

    async def _capture_network_requests_with_interaction(
        self, url: str, instructions: str
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Use Playwright to capture network requests while performing interactions based on instructions
        """
        requests = []
        html_content = ""

        async with async_playwright() as p:
            # Launch browser with additional options to handle complex sites like Zhihu
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Speed up loading for API detection
                ]
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                    'accept-encoding': 'gzip, deflate, br',
                    'dnt': '1',
                    'upgrade-insecure-requests': '1',
                    'sec-fetch-dest': 'document',
                    'sec-fetch-mode': 'navigate',
                    'sec-fetch-site': 'none',
                    'sec-fetch-user': '?1',
                    'cache-control': 'max-age=0',
                }
            )
            page = await context.new_page()

            # Add comprehensive stealth scripts to avoid detection
            await page.add_init_script("""
                // Pass toString test
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Remove webdriver property from navigator
                delete navigator.__proto__.webdriver;

                // Override plugins to appear more realistic
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'zh-CN'],
                });

                // Override chrome
                if (navigator.webdriver) {
                    delete Object.getOwnPropertyDescriptor(navigator, 'webdriver');
                }
            """)

            # Track requests
            async def handle_request_finished(request):
                try:
                    response = await request.response()
                    response_text = None
                    if response:
                        # Only capture successful responses
                        if 200 <= response.status < 300:
                            try:
                                response_text = await response.text()
                            except Exception:
                                # Some responses might not be text (e.g., binary data)
                                response_text = f"[Binary response of {response.headers.get('content-length', 'unknown')} bytes]"

                    # Filter out static resources
                    resource_type = request.resource_type
                    if resource_type not in ['stylesheet', 'image', 'media', 'font']:
                        requests.append({
                            "url": request.url,
                            "method": request.method,
                            "resource_type": resource_type,
                            "response": response_text,
                            "headers": await request.all_headers() if hasattr(request, 'all_headers') else {},
                            "status": response.status if response else None
                        })
                except Exception as e:
                    # Skip requests that cause errors
                    print(f"Warning: Error capturing request {request.url if 'request' in locals() else 'unknown'}: {e}")
                    pass

            page.on("requestfinished", handle_request_finished)

            try:
                # Navigate to the initial URL with more conservative settings
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Wait for additional network idle time
                await page.wait_for_timeout(3000)  # Wait 3 seconds for JS to load

                # Perform interactions based on instructions
                await self._perform_interactions(page, instructions)

                # Wait for any additional network activity after interactions
                await page.wait_for_timeout(2000)  # Wait 2 seconds after interactions

                # Get the final HTML content
                try:
                    html_content = await page.content()
                except:
                    # If content retrieval fails, use what we have
                    html_content = ""

            except Exception as e:
                # Continue even if page load or interaction fails
                print(f"Warning: Error during page interaction: {e}")
                try:
                    html_content = await page.content() if page else ""
                except:
                    html_content = ""
            finally:
                try:
                    await browser.close()
                except:
                    pass  # Browser might already be closed due to crash

        return requests, html_content

    async def _perform_interactions(self, page, instructions: str):
        """
        Perform interactions based on natural language instructions
        In a real implementation, this would use an LLM to convert instructions to Playwright operations
        """
        # This is a simplified version - in a real implementation,
        # an LLM would convert natural language to specific Playwright operations
        instructions_lower = instructions.lower()

        # Example: Look for common interaction patterns in the instructions
        if 'search' in instructions_lower and 'enter' in instructions_lower:
            # Look for search box and fill it
            search_selectors = ['#search', '#search-box', '[name="q"]', '[name="search"]', '.search-input']
            for selector in search_selectors:
                try:
                    if await page.query_selector(selector):
                        # Extract search term from instructions
                        search_match = re.search(r"['\"]([^'\"]*?)['\"].*?(?:in|to|into).*?search", instructions, re.IGNORECASE)
                        if search_match:
                            search_term = search_match.group(1)
                            await page.fill(selector, search_term)
                            break
                except:
                    continue

        # Look for click actions
        if 'click' in instructions_lower or 'button' in instructions_lower:
            # Look for execute/search buttons
            button_selectors = ['button', '[type="submit"]', '.btn', '.button']
            for selector in button_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text = await element.text_content()
                        if any(trigger in text.lower() for trigger in ['search', 'execute', 'submit', 'go']):
                            await element.click()
                            await page.wait_for_load_state('networkidle')
                            break
                except:
                    continue

    def _analyze_requests_intelligently(
        self, requests_data: List[Dict], keywords: List[str], data_description: str
    ) -> Tuple[List[APIEndpoint], Optional[str]]:
        """
        Analyze requests intelligently with LLM-assisted matching
        """
        api_endpoints = []
        pagination_api = None

        # Priority 1: Document (HTML) - Check for embedded JSON
        html_requests = [req for req in requests_data if req['resource_type'] == 'document']
        for req in html_requests:
            endpoints = self._find_embedded_json_in_html(req, keywords, data_description)
            api_endpoints.extend(endpoints)

        # Priority 2: XHR/Fetch requests with JSON content
        xhr_requests = [req for req in requests_data
                       if req['resource_type'] in ['xhr', 'fetch'] and req.get('response')]
        for req in xhr_requests:
            if req.get('response') and self._is_json_response(req):
                # Check if this is a pagination API
                if self._is_pagination_request(req['url']):
                    pagination_api = req['url']

                endpoints = self._analyze_json_response_intelligently(req, keywords, data_description)
                api_endpoints.extend(endpoints)

        # Priority 3: JS files that might contain stringified JSON
        js_requests = [req for req in requests_data
                      if req['resource_type'] == 'script' and req.get('response')]
        for req in js_requests:
            endpoints = self._analyze_js_for_json(req, keywords, data_description)
            api_endpoints.extend(endpoints)

        # Priority 4: Other text responses
        other_requests = [req for req in requests_data
                         if req['resource_type'] not in ['document', 'xhr', 'fetch', 'script']
                         and req.get('response')]
        for req in other_requests:
            endpoints = self._analyze_text_response(req, keywords, data_description)
            api_endpoints.extend(endpoints)

        # Sort by priority score (descending)
        api_endpoints.sort(key=lambda x: x.priority_score, reverse=True)

        return api_endpoints, pagination_api

    def _find_embedded_json_in_html(self, request: Dict, keywords: List[str], data_description: str) -> List[APIEndpoint]:
        """
        Find embedded JSON in HTML documents (e.g., Next.js __NEXT_DATA__)
        """
        endpoints = []
        response_text = request.get('response', '')

        # Handle case where response is None
        if response_text is None:
            response_text = ''

        # Look for common embedded JSON patterns
        patterns = [
            r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',  # Next.js
            r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',  # Generic JSON script tags
            r'window\.__DATA__\s*=\s*(\{.*?\});?',  # Common data assignment
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the JSON string
                    clean_match = match.strip()
                    if clean_match.startswith('/*') and clean_match.endswith('*/'):
                        clean_match = clean_match[2:-2].strip()

                    # Try to parse as JSON
                    parsed_json = json.loads(clean_match)
                    json_str = json.dumps(parsed_json, indent=2)[:500]  # Sample response

                    # Check if keywords match and calculate priority
                    match_result, score = self._calculate_match_score(json_str, keywords, data_description)
                    if match_result:
                        endpoint = APIEndpoint(
                            url=request['url'],
                            method=request['method'],
                            priority_score=score,
                            matched_fields=match_result,
                            sample_data=parsed_json if isinstance(parsed_json, dict) else {"data": parsed_json},
                            direct_use_example=f"Data embedded in HTML: {request['url']}"
                        )
                        endpoints.append(endpoint)
                except json.JSONDecodeError:
                    # Skip if not valid JSON
                    continue

        return endpoints

    def _analyze_json_response_intelligently(self, request: Dict, keywords: List[str], data_description: str) -> List[APIEndpoint]:
        """
        Analyze JSON responses with intelligent matching
        """
        endpoints = []
        response_text = request.get('response', '')

        # Handle case where response is None
        if response_text is None:
            return endpoints

        try:
            # Parse the JSON response
            parsed_json = json.loads(response_text)

            # Calculate match score and matched fields
            match_result, score = self._calculate_match_score(response_text, keywords, data_description)

            if match_result:
                endpoint = APIEndpoint(
                    url=request['url'],
                    method=request['method'],
                    priority_score=score,
                    matched_fields=match_result,
                    sample_data=parsed_json if isinstance(parsed_json, dict) else {"data": parsed_json},
                    direct_use_example=f"curl -X {request['method']} '{request['url']}'"
                )
                endpoints.append(endpoint)
        except json.JSONDecodeError:
            # Skip if not valid JSON
            pass

        return endpoints

    def _calculate_match_score(self, content: str, keywords: List[str], data_description: str) -> Tuple[List[str], float]:
        """
        Calculate a match score based on how well content matches the data description
        This is a simplified version - in a real implementation, an LLM would be used
        """
        content_lower = content.lower()
        matched_keywords = []

        for keyword in keywords:
            if keyword.lower() in content_lower:
                matched_keywords.append(keyword)

        # Calculate a simple score based on number of matched keywords
        score = min(len(matched_keywords) / max(len(keywords), 1), 1.0)

        # Boost score if content looks like structured data (JSON)
        if '{' in content and '}' in content:
            score = min(score + 0.2, 1.0)

        return matched_keywords, score

    def _analyze_js_for_json(self, request: Dict, keywords: List[str], data_description: str) -> List[APIEndpoint]:
        """
        Analyze JS files for stringified JSON that might contain relevant data
        """
        endpoints = []
        response_text = request.get('response', '')

        # Handle case where response is None
        if response_text is None:
            return endpoints

        # Look for JSON-parse calls or stringified JSON objects
        json_patterns = [
            r'JSON\.parse\s*\(\s*[\'"`](\{.*?\})[\'"`]\s*\)',  # JSON.parse('{"key": "value"}')
            r'JSON\.parse\s*\(\s*`(\{.*?\})`\s*\)',  # JSON.parse(`{"key": "value"}`)
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the JSON string
                    clean_match = match.strip()
                    parsed_json = json.loads(clean_match)
                    json_str = json.dumps(parsed_json, indent=2)[:500]  # Sample response

                    # Check if keywords match and calculate priority
                    match_result, score = self._calculate_match_score(json_str, keywords, data_description)
                    if match_result:
                        endpoint = APIEndpoint(
                            url=request['url'],
                            method=request['method'],
                            priority_score=score,
                            matched_fields=match_result,
                            sample_data=parsed_json if isinstance(parsed_json, dict) else {"data": parsed_json},
                            direct_use_example=f"JS file contains data: {request['url']}"
                        )
                        endpoints.append(endpoint)
                except json.JSONDecodeError:
                    # Skip if not valid JSON
                    continue

        return endpoints

    def _analyze_text_response(self, request: Dict, keywords: List[str], data_description: str) -> List[APIEndpoint]:
        """
        Analyze text responses for structured data
        """
        endpoints = []
        response_text = request.get('response', '')

        # Handle case where response is None
        if response_text is None:
            return endpoints

        # Check if keywords match and calculate priority
        match_result, score = self._calculate_match_score(response_text, keywords, data_description)
        if match_result:
            content_type = request.get('headers', {}).get('content-type', 'text/plain')

            endpoint = APIEndpoint(
                url=request['url'],
                method=request['method'],
                priority_score=score,
                matched_fields=match_result,
                sample_data={"content_preview": response_text[:200]},
                direct_use_example=f"curl -X {request['method']} '{request['url']}'"
            )
            endpoints.append(endpoint)

        return endpoints

    def _is_json_response(self, request: Dict) -> bool:
        """
        Check if a response is JSON based on content-type header
        """
        headers = request.get('headers', {})
        content_type = headers.get('content-type', headers.get('Content-Type', ''))
        return 'application/json' in content_type.lower()

    def _is_pagination_request(self, url: str) -> bool:
        """
        Check if a URL represents a pagination request
        """
        pagination_patterns = [
            r'[?&]page=\d+',
            r'[?&]p=\d+',
            r'/page/\d+',
            r'/\d+/page',
        ]

        for pattern in pagination_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        return False

    async def _generate_fallback_selectors(self, html_content: str, data_description: str) -> Dict[str, List[Dict]]:
        """
        Generate CSS selectors as fallback when no APIs are found
        """
        if not html_content:
            return {"if_no_api": []}

        soup = BeautifulSoup(html_content, 'html.parser')

        # Check if this is a security verification page (anti-bot page)
        title_tag = soup.find('title')
        if title_tag and '安全验证' in title_tag.get_text():
            return {
                "if_no_api": [{
                    "element": "Security Verification Detected",
                    "selector": "title",
                    "example": "Detected security verification page - access blocked by anti-bot measures"
                }],
                "anti_bot_detected": True,
                "suggestion": "Try using proxies, rotating user agents, or solving captcha manually"
            }

        # This is a simplified version - in a real implementation,
        # an LLM would analyze the HTML structure and generate appropriate selectors
        selectors = []

        # Enhanced selector generation for different types of content
        # Look for common article/content containers
        item_selectors = ['.ArticleItem', '.Post-Main', '.RichContent-inner', '.ContentItem', '.Article', '.post', '.entry-content', '.article-body']

        # Specific selectors for Zhihu articles
        zhihu_selectors = [
            ('Title', '.Post-Title', 'h1'),
            ('Content', '.Post-RichTextContainer', '.RichContent-inner', '.Post-Header'),
            ('Author', '.UserLink-link', '.AuthorInfo-name'),
            ('Publish Date', '.ContentItem-time', '.Post-meta', '.RichContent-meta'),
            ('Comments', '.Comments-section', '.Comment', '.DiscussSection'),
        ]

        # Process Zhihu-specific selectors
        for field_name, *css_selectors in zhihu_selectors:
            for css_selector in css_selectors:
                elements = soup.select(css_selector)
                if elements:
                    example_html = str(elements[0])[:100]  # First 100 chars as example
                    selectors.append({
                        "element": field_name,
                        "selector": css_selector,
                        "example": example_html
                    })
                    break  # Move to next field once we find a match

        # General selectors for other fields mentioned in data_description
        field_names = re.findall(r'\b(\w+)\b', data_description.lower())
        for field in field_names:
            if field not in [sel['element'].lower() for sel in selectors]:  # Avoid duplicates
                # Look for elements that might contain this field
                field_selectors = soup.select(f'.{field}, [class*="{field}"], [id*="{field}"], h1, h2, h3, .author, .pub-date, .meta, .time, .name')
                if field_selectors:
                    example_html = str(field_selectors[0])[:100]  # First 100 chars as example
                    selectors.append({
                        "element": field.title(),
                        "selector": field_selectors[0].name if field_selectors else f'.{field}',
                        "example": example_html
                    })

        return {"if_no_api": selectors}

    def _extract_links_for_next_depth(self, requests_data: List[Dict], base_url: str, include_pagination: bool) -> List[str]:
        """
        Extract links from the page that could be crawled at the next depth level
        """
        links = set()
        base_domain = urlparse(base_url).netloc

        # Look for links in HTML responses
        html_responses = [req for req in requests_data
                         if req['resource_type'] == 'document' and req.get('response')]

        for req in html_responses:
            response_text = req.get('response', '')

            # Extract href links
            href_pattern = r'<a[^>]+href=["\']([^"\']+)["\']'
            href_matches = re.findall(href_pattern, response_text, re.IGNORECASE)

            for href in href_matches:
                # Resolve relative URLs
                full_url = urljoin(req['url'], href)
                link_domain = urlparse(full_url).netloc

                # Only include same-domain links
                if link_domain == base_domain:
                    # Skip if it's a pagination link and we're not including pagination
                    if not include_pagination and self._is_pagination_request(full_url):
                        continue

                    # Skip sensitive paths
                    if any(sensitive in full_url.lower() for sensitive in ['/auth/', '/login/', '/admin/']):
                        continue

                    links.add(full_url)

        return list(links)

    def _api_to_dict(self, api: APIEndpoint) -> Dict[str, Any]:
        """
        Convert APIEndpoint dataclass to dictionary
        """
        return {
            "url": api.url,
            "method": api.method,
            "priority_score": api.priority_score,
            "matched_fields": api.matched_fields,
            "sample_data": api.sample_data,
            "direct_use_example": api.direct_use_example
        }


def webapi_crawler_analyzer_skill(
    instructions: str, 
    data_description: str, 
    max_depth: int = 1, 
    confirm_each_depth: bool = True, 
    include_pagination: bool = False
) -> Dict[str, Any]:
    """
    Main function to be called by an LLM to analyze web APIs using natural language instructions.
    
    Args:
        instructions: Natural language instructions including URL and actions
        data_description: Description of the data you want to extract
        max_depth: Maximum crawling depth (0 means only current page)
        confirm_each_depth: Whether to confirm before proceeding to next depth level
        include_pagination: Whether to treat pagination links as next level
    
    Returns:
        Dictionary with API analysis results
    """
    try:
        # Create analyzer instance with provided parameters
        analyzer = WebAPICrawlerAnalyzer(
            max_depth=max_depth,
            confirm_each_depth=confirm_each_depth,
            include_pagination=include_pagination
        )
        
        # Run the analysis asynchronously
        result = asyncio.run(analyzer.analyze(instructions, data_description))
        
        return result
    except Exception as e:
        # Return error in a consistent format
        return {
            "execution_summary": f"Error during analysis: {str(e)}",
            "recommended_apis": [],
            "fallback_html_selectors": {"if_no_api": []},
            "next_actions": {
                "requires_confirmation": False,
                "available_depth_links": [],
                "pagination_api_detected": None
            }
        }


# For backward compatibility and testing purposes
async def main():
    """
    Example usage of the WebAPI Crawler Analyzer
    """
    # Example usage
    analyzer = WebAPICrawlerAnalyzer(max_depth=1, confirm_each_depth=True, include_pagination=False)

    result = await analyzer.analyze(
        instructions="Open https://example-commerce.com/products, enter 'phone' in search box, click search button",
        data_description="product names, prices, inventory status"
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())