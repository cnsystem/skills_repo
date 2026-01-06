#!/usr/bin/env python3
"""
WebAPI Crawler Analyzer
A script to intelligently identify crawlable WebAPI endpoints from web pages
and handle multi-level page crawling with depth control.
"""

import asyncio
import json
import re
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import nltk  # For keyword extraction
from playwright.async_api import async_playwright


@dataclass
class APIEndpoint:
    url: str
    method: str
    content_type: str
    matched_keywords: List[str]
    priority_level: int
    sample_response: str


class WebAPICrawlerAnalyzer:
    def __init__(self, max_depth: int = 1, confirm_each_depth: bool = True):
        self.max_depth = max_depth
        self.confirm_each_depth = confirm_each_depth
        self.crawled_urls = set()
        self.visited_domains = set()
        
    async def analyze(self, url: str, data_description: str) -> Dict[str, Any]:
        """
        Main method to analyze a URL and find relevant API endpoints
        """
        # Extract keywords from data description
        keywords = self._extract_keywords(data_description)
        
        # Perform the crawling analysis
        result = await self._crawl_and_analyze(url, keywords, depth=0)
        
        return result
    
    def _extract_keywords(self, data_description: str) -> List[str]:
        """
        Extract keywords from the data description for matching
        """
        # Simple keyword extraction - in a real implementation, 
        # we might use NLP techniques for better accuracy
        keywords = re.findall(r'\b\w+\b', data_description.lower())
        return [kw for kw in keywords if len(kw) > 2]  # Filter out short words
    
    async def _crawl_and_analyze(self, url: str, keywords: List[str], depth: int) -> Dict[str, Any]:
        """
        Recursively crawl and analyze URLs up to max_depth
        """
        if depth >= self.max_depth or url in self.crawled_urls:
            return {
                "analyzed_apis": [],
                "next_depth_links": [],
                "requires_user_confirmation": False,
                "analysis_summary": f"Reached max depth ({self.max_depth}) or already crawled"
            }
        
        self.crawled_urls.add(url)
        
        # Capture network requests using Playwright
        requests_data = await self._capture_network_requests(url)
        
        # Analyze requests by priority
        analyzed_apis = self._analyze_requests_by_priority(requests_data, keywords)
        
        # Extract links for next depth level
        next_depth_links = self._extract_links_for_next_depth(requests_data, url)
        
        # Check if we need user confirmation for next depth
        requires_confirmation = (
            self.confirm_each_depth 
            and depth + 1 < self.max_depth 
            and next_depth_links
        )
        
        # Prepare analysis summary
        summary_parts = []
        if analyzed_apis:
            summary_parts.append(f"Found {len(analyzed_apis)} API endpoints")
        if next_depth_links:
            summary_parts.append(f"Discovered {len(next_depth_links)} links for next depth")
        
        analysis_summary = ". ".join(summary_parts) or "No significant findings"
        
        result = {
            "analyzed_apis": [self._api_to_dict(api) for api in analyzed_apis],
            "next_depth_links": next_depth_links[:10],  # Limit to first 10 for display
            "requires_user_confirmation": requires_confirmation,
            "analysis_summary": analysis_summary
        }
        
        return result
    
    async def _capture_network_requests(self, url: str) -> List[Dict[str, Any]]:
        """
        Use Playwright to capture all network requests made during page load
        """
        requests = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Track requests
            async def handle_request_finished(request):
                try:
                    response = await request.response()
                    response_text = None
                    if response:
                        # Only capture successful responses
                        if response.status == 200:
                            response_text = await response.text()
                    
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
                except Exception:
                    # Skip requests that cause errors
                    pass
            
            page.on("requestfinished", handle_request_finished)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)  # Allow dynamic content to load
            except Exception:
                # Continue even if page load times out
                pass
            finally:
                await browser.close()
        
        return requests
    
    def _analyze_requests_by_priority(self, requests_data: List[Dict], keywords: List[str]) -> List[APIEndpoint]:
        """
        Analyze requests by priority to find the most relevant APIs
        """
        api_endpoints = []
        
        # Priority 1: Document (HTML) - Check for embedded JSON
        html_requests = [req for req in requests_data if req['resource_type'] == 'document']
        for req in html_requests:
            endpoints = self._find_embedded_json_in_html(req, keywords)
            api_endpoints.extend(endpoints)
        
        # Priority 2: XHR/Fetch requests with JSON content
        xhr_requests = [req for req in requests_data 
                       if req['resource_type'] in ['xhr', 'fetch'] and req.get('response')]
        for req in xhr_requests:
            if req.get('response') and self._is_json_response(req):
                endpoints = self._analyze_json_response(req, keywords)
                api_endpoints.extend(endpoints)
        
        # Priority 3: JS files that might contain stringified JSON
        js_requests = [req for req in requests_data 
                      if req['resource_type'] == 'script' and req.get('response')]
        for req in js_requests:
            endpoints = self._analyze_js_for_json(req, keywords)
            api_endpoints.extend(endpoints)
        
        # Priority 4: Other text responses
        other_requests = [req for req in requests_data 
                         if req['resource_type'] not in ['document', 'xhr', 'fetch', 'script'] 
                         and req.get('response')]
        for req in other_requests:
            endpoints = self._analyze_text_response(req, keywords)
            api_endpoints.extend(endpoints)
        
        return api_endpoints
    
    def _find_embedded_json_in_html(self, request: Dict, keywords: List[str]) -> List[APIEndpoint]:
        """
        Find embedded JSON in HTML documents (e.g., Next.js __NEXT_DATA__)
        """
        endpoints = []
        response_text = request.get('response', '')
        
        # Look for common embedded JSON patterns
        patterns = [
            r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',  # Next.js
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
                    
                    # Check if keywords match
                    match_result = self._check_keywords_in_content(json_str, keywords)
                    if match_result:
                        endpoint = APIEndpoint(
                            url=request['url'],
                            method=request['method'],
                            content_type='application/json',
                            matched_keywords=match_result,
                            priority_level=1,
                            sample_response=json_str
                        )
                        endpoints.append(endpoint)
                except json.JSONDecodeError:
                    # Skip if not valid JSON
                    continue
        
        return endpoints
    
    def _analyze_json_response(self, request: Dict, keywords: List[str]) -> List[APIEndpoint]:
        """
        Analyze JSON responses for keyword matches
        """
        endpoints = []
        response_text = request.get('response', '')
        
        # Check if keywords match in the response
        match_result = self._check_keywords_in_content(response_text, keywords)
        if match_result:
            endpoint = APIEndpoint(
                url=request['url'],
                method=request['method'],
                content_type='application/json',
                matched_keywords=match_result,
                priority_level=2,
                sample_response=response_text[:500]  # First 500 chars as sample
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _analyze_js_for_json(self, request: Dict, keywords: List[str]) -> List[APIEndpoint]:
        """
        Analyze JS files for stringified JSON that might contain relevant data
        """
        endpoints = []
        response_text = request.get('response', '')
        
        # Look for JSON.parse calls or stringified JSON objects
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
                    
                    # Check if keywords match
                    match_result = self._check_keywords_in_content(json_str, keywords)
                    if match_result:
                        endpoint = APIEndpoint(
                            url=request['url'],
                            method=request['method'],
                            content_type='application/json',
                            matched_keywords=match_result,
                            priority_level=3,
                            sample_response=json_str
                        )
                        endpoints.append(endpoint)
                except json.JSONDecodeError:
                    # Skip if not valid JSON
                    continue
        
        return endpoints
    
    def _analyze_text_response(self, request: Dict, keywords: List[str]) -> List[APIEndpoint]:
        """
        Analyze text responses for structured data
        """
        endpoints = []
        response_text = request.get('response', '')
        
        # Check if keywords match in the response
        match_result = self._check_keywords_in_content(response_text, keywords)
        if match_result:
            content_type = request.get('headers', {}).get('content-type', 'text/plain')
            endpoint = APIEndpoint(
                url=request['url'],
                method=request['method'],
                content_type=content_type,
                matched_keywords=match_result,
                priority_level=4,
                sample_response=response_text[:500]  # First 500 chars as sample
            )
            endpoints.append(endpoint)
        
        return endpoints
    
    def _check_keywords_in_content(self, content: str, keywords: List[str]) -> List[str]:
        """
        Check if any of the keywords appear in the content
        """
        content_lower = content.lower()
        matched_keywords = []
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                matched_keywords.append(keyword)
        
        return matched_keywords
    
    def _is_json_response(self, request: Dict) -> bool:
        """
        Check if a response is JSON based on content-type header
        """
        headers = request.get('headers', {})
        content_type = headers.get('content-type', headers.get('Content-Type', ''))
        return 'application/json' in content_type.lower()
    
    def _extract_links_for_next_depth(self, requests_data: List[Dict], base_url: str) -> List[str]:
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
                    links.add(full_url)
        
        return list(links)
    
    def _api_to_dict(self, api: APIEndpoint) -> Dict[str, Any]:
        """
        Convert APIEndpoint dataclass to dictionary
        """
        return {
            "url": api.url,
            "method": api.method,
            "content_type": api.content_type,
            "matched_keywords": api.matched_keywords,
            "priority_level": api.priority_level,
            "sample_response": api.sample_response
        }


async def main():
    """
    Example usage of the WebAPI Crawler Analyzer
    """
    # Example usage
    analyzer = WebAPICrawlerAnalyzer(max_depth=2, confirm_each_depth=True)
    
    result = await analyzer.analyze(
        url="https://example-commerce.com/products",
        data_description="product names, prices, inventory status"
    )
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())