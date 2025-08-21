#!/usr/bin/env python3
"""
Configuration file for TikTok Shop scraper
"""

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ScrapingConfig:
    """Configuration for scraping parameters"""
    
    # Target markets
    MARKETS = {
        'vietnam': {
            'code': 'vn',
            'language': 'vi-VN',
            'currency': 'VND',
            'timezone': 'Asia/Ho_Chi_Minh'
        },
        'saudi_arabia': {
            'code': 'sa',
            'language': 'ar-SA',
            'currency': 'SAR',
            'timezone': 'Asia/Riyadh'
        }
    }
    
    # Target brand
    TARGET_BRAND = 'lancome'
    
    # Scraping parameters
    HEADLESS_BROWSER = True
    MAX_PRODUCTS_PER_MARKET = 20
    MAX_REVIEWS_PER_PRODUCT = 100
    
    # Delays (in seconds)
    MIN_DELAY = 1.0
    MAX_DELAY = 3.0
    PRODUCT_DELAY_MIN = 5.0
    PRODUCT_DELAY_MAX = 10.0
    
    # Timeouts
    PAGE_LOAD_TIMEOUT = 30
    ELEMENT_WAIT_TIMEOUT = 10
    
    # Output files
    OUTPUT_CSV = "aymane_aallaoui_tiktok_shop_reviews_sample.csv"
    LOG_FILE = "scraper.log"
    
    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0'
    ]
    
    # CSS Selectors (may need updates based on site changes)
    SELECTORS = {
        'product_cards': [
            '.product-card',
            '[data-testid*="product"]',
            '.item-card',
            '.goods-card',
            'a[href*="/product/"]'
        ],
        'product_title': [
            'h1',
            '.product-title',
            '[data-testid*="title"]',
            '.goods-title'
        ],
        'product_price': [
            '.price',
            '.product-price',
            '.cost',
            '[data-testid*="price"]'
        ],
        'reviews_section': [
            '.reviews-section',
            '.review-list',
            '[data-testid*="review"]',
            '.comment-section'
        ],
        'review_items': [
            '.review-item',
            '.comment-item',
            '.feedback-item',
            '[data-testid*="review-item"]'
        ],
        'reviewer_name': [
            '.reviewer-name',
            '.username',
            '.author',
            '[data-testid*="username"]'
        ],
        'review_rating': [
            '.rating',
            '.star-rating',
            '.score',
            '[data-testid*="rating"]'
        ],
        'review_text': [
            '.review-text',
            '.comment-text',
            '.content',
            '[data-testid*="content"]'
        ],
        'review_date': [
            '.review-date',
            '.timestamp',
            '.date',
            '[data-testid*="date"]'
        ],
        'load_more_buttons': [
            '.load-more',
            '.show-more',
            'button[data-testid*="load"]'
        ]
    }
    
    # Proxy settings (if needed)
    PROXY = os.getenv('PROXY_URL')  # Format: 'http://user:pass@host:port'
    
    # Chrome options
    CHROME_OPTIONS = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-images',  # Faster loading
        '--disable-javascript',  # May break some functionality
    ]
    
    # Rate limiting
    REQUESTS_PER_MINUTE = 10
    CONCURRENT_REQUESTS = 1
    
    # Error handling
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    # Data validation
    MIN_REVIEW_LENGTH = 10  # Minimum characters for valid review
    MAX_REVIEW_LENGTH = 5000  # Maximum characters
    

# Environment-specific configurations
DEVELOPMENT_CONFIG = ScrapingConfig()
DEVELOPMENT_CONFIG.HEADLESS_BROWSER = False
DEVELOPMENT_CONFIG.MAX_PRODUCTS_PER_MARKET = 5
DEVELOPMENT_CONFIG.MIN_DELAY = 2.0
DEVELOPMENT_CONFIG.MAX_DELAY = 5.0

PRODUCTION_CONFIG = ScrapingConfig()
PRODUCTION_CONFIG.HEADLESS_BROWSER = True
PRODUCTION_CONFIG.MAX_PRODUCTS_PER_MARKET = 50
PRODUCTION_CONFIG.MIN_DELAY = 3.0
PRODUCTION_CONFIG.MAX_DELAY = 8.0

# Get configuration based on environment
def get_config():
    env = os.getenv('ENVIRONMENT', 'development').lower()
    if env == 'production':
        return PRODUCTION_CONFIG
    return DEVELOPMENT_CONFIG
