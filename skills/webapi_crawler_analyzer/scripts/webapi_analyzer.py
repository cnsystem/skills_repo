#!/usr/bin/env python3
"""
WebAPI Crawler Analyzer - Simplified Implementation
A script to capture web requests and responses with event injection
for natural language instructions, leaving analysis to LLM.
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Tuple
from playwright.async_api import async_playwright


class WebAPICrawlerAnalyzer:
    def __init__(self):
        pass

    async def analyze(self, instructions: str) -> Dict[str, Any]:
        """
        Main method to capture web requests and responses based on natural language instructions
        """
        # Extract URL from instructions
        url = self._extract_url_from_instructions(instructions)

        # Capture network requests using Playwright with interactions
        requests_data, html_content = await self._capture_network_requests_with_interaction(
            url, instructions
        )

        # Return raw data for LLM analysis
        result = {
            "execution_summary": f"Captured {len(requests_data)} network requests and HTML content",
            "raw_requests_data": requests_data,
            "html_content": html_content,
            "instructions_used": instructions
        }

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

    async def _capture_network_requests_with_interaction(
        self, url: str, instructions: str
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Use Playwright to capture network requests while performing interactions based on instructions
        """
        requests = []
        html_content = ""

        async with async_playwright() as p:
            # Launch browser with additional options to handle complex sites
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


def webapi_crawler_analyzer_skill(
    instructions: str
) -> Dict[str, Any]:
    """
    Main function to be called by an LLM to capture web requests/responses using natural language instructions.

    Args:
        instructions: Natural language instructions including URL and actions

    Returns:
        Dictionary with raw captured data for LLM analysis
    """
    try:
        # Create analyzer instance
        analyzer = WebAPICrawlerAnalyzer()

        # Run the analysis asynchronously
        result = asyncio.run(analyzer.analyze(instructions))

        return result
    except Exception as e:
        # Return error in a consistent format
        return {
            "execution_summary": f"Error during analysis: {str(e)}",
            "raw_requests_data": [],
            "html_content": "",
            "instructions_used": instructions
        }


# For backward compatibility and testing purposes
async def main():
    """
    Example usage of the WebAPI Crawler Analyzer
    """
    # Example usage
    analyzer = WebAPICrawlerAnalyzer()

    result = await analyzer.analyze(
        instructions="Open https://httpbin.org/get, click any button if present"
    )

    print(json.dumps(result, indent=2))


