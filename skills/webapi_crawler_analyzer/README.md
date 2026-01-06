# WebAPI Crawler Analyzer Skill - Updated

This skill provides advanced intelligent web API discovery and analysis capabilities using natural language instructions and Playwright for browser automation.

## Overview

The `webapi_crawler_analyzer` skill is designed to:
- Discover API endpoints from web pages using natural language instructions
- Perform dynamic interactions (fill forms, click buttons) based on user instructions
- Analyze network requests to identify data sources that match user requirements
- Handle pagination scenarios intelligently
- Perform fallback HTML parsing when no APIs are found
- Provide LLM-assisted matching for better relevance

## Key Features

- **Natural Language Interface**: Provide instructions in plain English
- **Dynamic Interaction**: Fill forms, click buttons, and interact with pages
- **Intelligent API Discovery**: Prioritizes XHR requests and uses scoring algorithms
- **Pagination Handling**: Special processing for paginated content
- **Fallback Parsing**: Generates CSS selectors when no APIs are available
- **Depth Control**: Configurable crawling depth with confirmation options
- **Safety Mechanisms**: Rate limiting, timeout controls, and privacy protection

## Components

- `SKILL.md`: Main skill definition with usage instructions
- `scripts/webapi_analyzer.py`: Core implementation with natural language processing
- `references/implementation_details.md`: Detailed technical documentation
- `assets/example_input_output.json`: Example usage patterns

## Usage

The skill can be invoked with parameters specifying:
- Natural language `instructions` with URL and actions
- `data_description` of desired data
- `max_depth` for crawling (0 = current page only)
- `confirm_each_depth` for multi-level crawling
- `include_pagination` for pagination handling

## Requirements

- Python 3.7+
- Playwright library
- BeautifulSoup4 for HTML parsing fallback
- Network access to target websites