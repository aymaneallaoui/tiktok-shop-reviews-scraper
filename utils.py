#!/usr/bin/env python3
"""
Utility functions for TikTok Shop scraper
"""

import re
import time
import random
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
from urllib.parse import urlparse, urljoin


def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might cause CSV issues
    text = text.replace('"', '""')  # Escape quotes for CSV
    text = re.sub(r'[\r\n]+', ' ', text)  # Replace newlines with spaces
    
    return text


def extract_number_from_text(text: str) -> Optional[float]:
    """Extract numeric value from text (for ratings, prices, etc.)"""
    if not text:
        return None
        
    # Remove common currency symbols and text
    cleaned = re.sub(r'[^\d.,]', '', text)
    
    try:
        # Handle different decimal separators
        if ',' in cleaned and '.' in cleaned:
            # Assume comma is thousands separator
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Could be decimal separator in some locales
            cleaned = cleaned.replace(',', '.')
            
        return float(cleaned)
    except ValueError:
        return None


def normalize_rating(rating_text: str) -> str:
    """Normalize rating to standard format"""
    if not rating_text:
        return "N/A"
        
    # Extract numeric rating
    number = extract_number_from_text(rating_text)
    if number is not None:
        return str(round(number, 1))
        
    # Handle star ratings
    star_count = rating_text.count('★') + rating_text.count('⭐')
    if star_count > 0:
        return str(star_count)
        
    return rating_text


def normalize_date(date_text: str) -> str:
    """Normalize date to ISO format if possible"""
    if not date_text:
        return "N/A"
        
    # Common date patterns
    patterns = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{2})/(\d{2})/(\d{4})',  # MM/DD/YYYY
        r'(\d{2})\.(\d{2})\.(\d{4})', # DD.MM.YYYY
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_text)
        if match:
            try:
                if 'YYYY-MM-DD' in pattern:
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                elif 'MM/DD/YYYY' in pattern:
                    return f"{match.group(3)}-{match.group(1).zfill(2)}-{match.group(2).zfill(2)}"
                elif 'DD.MM.YYYY' in pattern:
                    return f"{match.group(3)}-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
            except:
                continue
                
    return date_text


def generate_review_id(reviewer_name: str, review_text: str, date: str, product_url: str) -> str:
    """Generate unique review ID"""
    content = f"{reviewer_name}{review_text}{date}{product_url}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def make_absolute_url(base_url: str, relative_url: str) -> str:
    """Convert relative URL to absolute URL"""
    if is_valid_url(relative_url):
        return relative_url
    return urljoin(base_url, relative_url)


def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """Add random delay"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def get_random_user_agent() -> str:
    """Get random user agent string"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0'
    ]
    return random.choice(user_agents)


def validate_review_data(review_data: Dict) -> bool:
    """Validate review data quality"""
    required_fields = ['product_url', 'reviewer_name', 'review_text']
    
    # Check required fields
    for field in required_fields:
        if not review_data.get(field):
            return False
            
    # Validate review text length
    review_text = review_data.get('review_text', '')
    if len(review_text) < 10 or len(review_text) > 5000:
        return False
        
    # Validate URL
    if not is_valid_url(review_data.get('product_url', '')):
        return False
        
    return True


def deduplicate_reviews(reviews: List[Dict]) -> List[Dict]:
    """Remove duplicate reviews based on content similarity"""
    seen_reviews = set()
    unique_reviews = []
    
    for review in reviews:
        # Create a hash based on key fields
        review_hash = generate_review_id(
            review.get('reviewer_name', ''),
            review.get('review_text', ''),
            review.get('review_date', ''),
            review.get('product_url', '')
        )
        
        if review_hash not in seen_reviews:
            seen_reviews.add(review_hash)
            unique_reviews.append(review)
            
    return unique_reviews


def create_progress_tracker():
    """Create a simple progress tracker"""
    class ProgressTracker:
        def __init__(self):
            self.start_time = time.time()
            self.total_products = 0
            self.processed_products = 0
            self.total_reviews = 0
            
        def update_products(self, total: int, processed: int):
            self.total_products = total
            self.processed_products = processed
            
        def add_reviews(self, count: int):
            self.total_reviews += count
            
        def get_stats(self) -> Dict:
            elapsed = time.time() - self.start_time
            return {
                'elapsed_minutes': round(elapsed / 60, 2),
                'products_processed': self.processed_products,
                'total_products': self.total_products,
                'total_reviews': self.total_reviews,
                'avg_reviews_per_product': round(self.total_reviews / max(self.processed_products, 1), 2)
            }
            
    return ProgressTracker()


def handle_rate_limiting(func):
    """Decorator for handling rate limiting"""
    def wrapper(*args, **kwargs):
        max_retries = 3
        base_delay = 5
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                    
                # Exponential backoff
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Rate limited, waiting {delay:.1f} seconds before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
                
    return wrapper


def save_checkpoint(data: List[Dict], filename: str = "checkpoint.json"):
    """Save progress checkpoint"""
    import json
    
    checkpoint = {
        'timestamp': datetime.now().isoformat(),
        'review_count': len(data),
        'data': data
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
        print(f"Checkpoint saved: {len(data)} reviews")
    except Exception as e:
        print(f"Failed to save checkpoint: {e}")


def load_checkpoint(filename: str = "checkpoint.json") -> List[Dict]:
    """Load progress checkpoint"""
    import json
    import os
    
    if not os.path.exists(filename):
        return []
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        print(f"Checkpoint loaded: {len(checkpoint.get('data', []))} reviews")
        return checkpoint.get('data', [])
    except Exception as e:
        print(f"Failed to load checkpoint: {e}")
        return []
