# WebAPI Crawler Analyzer Skill

This skill provides intelligent web API discovery and analysis capabilities using Playwright for browser automation and network request interception.

## Overview

The `webapi_crawler_analyzer` skill is designed to:
- Discover API endpoints from web pages
- Analyze network requests to identify data sources
- Extract structured data based on user-defined criteria
- Perform controlled-depth crawling with safety mechanisms

## Features

- **Intelligent API Discovery**: Uses Playwright to capture all network requests and analyze them by priority
- **Keyword Matching**: Matches responses against user-defined data descriptions
- **Depth Control**: Prevents infinite crawling loops with configurable depth limits
- **Safety Mechanisms**: Includes rate limiting, timeout controls, and data sanitization
- **Multi-format Support**: Handles JSON, embedded scripts, and other data formats

## Components

- `SKILL.md`: Main skill definition with usage instructions
- `scripts/webapi_analyzer.py`: Core implementation of the analyzer
- `references/implementation_details.md`: Detailed technical documentation
- `assets/example_input_output.json`: Example usage patterns

## Usage

The skill can be invoked with parameters specifying:
- Target URL to analyze
- Description of desired data
- Maximum crawling depth
- Confirmation preferences for multi-depth crawling

## Requirements

- Python 3.7+
- Playwright library
- Network access to target websites