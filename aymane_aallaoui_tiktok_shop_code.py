#!/usr/bin/env python3
"""
TikTok Shop Reviews Scraper for Lancôme Products
Technical Assessment - Data Scientist Position

Author: Aymane Aallaoui
Target Markets: Vietnam, Saudi Arabia
Target Brand: Lancôme
"""

import time
import csv
import json
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, quote
from dataclasses import dataclass, asdict

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


@dataclass
class ProductInfo:
    """Data class for product information"""
    url: str
    name: str
    price: str
    rating: str
    review_count: str
    brand: str
    market: str


@dataclass
class ReviewInfo:
    """Data class for review information"""
    product_url: str
    product_name: str
    reviewer_name: str
    rating: str
    review_text: str
    review_date: str
    verified_purchase: str
    helpful_votes: str
    review_id: str
    country_market: str
    scrape_timestamp: str


class TikTokShopScraper:
    """Main scraper class for TikTok Shop reviews"""
    
    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        self.setup_logging()
        self.markets = {
            'vietnam': 'vn',
            'saudi_arabia': 'sa'
        }
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.headless = headless
        self.proxy = proxy
        self.session = requests.Session()
        self.driver = None
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self, market: str) -> webdriver.Chrome:
        """Setup Chrome driver with appropriate options"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
            
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
        
        # Add proxy if provided
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
            
        # Market-specific configurations
        if market == 'vn':
            options.add_argument('--lang=vi-VN')
        elif market == 'sa':
            options.add_argument('--lang=ar-SA')
            
        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup driver: {e}")
            raise
            
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to avoid being detected as bot"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def get_tiktok_shop_url(self, market: str) -> str:
        """Get TikTok Shop URL for specific market"""
        market_code = self.markets.get(market)
        if not market_code:
            raise ValueError(f"Unsupported market: {market}")
        return f"https://shop.tiktok.com/{market_code}"
        
    def search_lancome_products(self, market: str) -> List[ProductInfo]:
        """Search for Lancôme products in specified market"""
        self.logger.info(f"Searching for Lancôme products in {market}")
        
        self.driver = self.setup_driver(market)
        products = []
        
        try:
            base_url = self.get_tiktok_shop_url(market)
            
            # Method 1: Direct brand search
            search_url = f"{base_url}/search?q={quote('lancome')}"
            self.logger.info(f"Accessing search URL: {search_url}")
            
            self.driver.get(search_url)
            self.random_delay(3, 5)
            
            # Wait for page to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "product-card"))
                )
            except TimeoutException:
                self.logger.warning("Product cards not found, trying alternative selectors")
                
            # Try multiple selectors for product cards
            product_selectors = [
                ".product-card",
                "[data-testid*='product']",
                ".item-card",
                ".goods-card",
                "a[href*='/product/']"
            ]
            
            product_elements = []
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        product_elements = elements
                        self.logger.info(f"Found {len(elements)} products with selector: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    
            if not product_elements:
                self.logger.warning("No product elements found, trying page source parsing")
                return self.parse_products_from_source(market)
                
            # Extract product information
            for element in product_elements[:20]:  # Limit to first 20 products
                try:
                    product = self.extract_product_info(element, market)
                    if product and 'lancome' in product.name.lower():
                        products.append(product)
                        self.logger.info(f"Found Lancôme product: {product.name}")
                except Exception as e:
                    self.logger.debug(f"Failed to extract product info: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error searching products in {market}: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                
        return products
        
    def parse_products_from_source(self, market: str) -> List[ProductInfo]:
        """Parse products from page source as fallback method"""
        products = []
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Look for links that might be product URLs
            links = soup.find_all('a', href=True)
            product_urls = []
            
            for link in links:
                href = link.get('href')
                if href and '/product/' in href:
                    if not href.startswith('http'):
                        href = urljoin(self.get_tiktok_shop_url(market), href)
                    product_urls.append(href)
                    
            # Visit each product URL to get details
            for url in product_urls[:10]:  # Limit to prevent timeout
                try:
                    self.driver.get(url)
                    self.random_delay(2, 4)
                    
                    # Extract product name to check for Lancôme
                    title_selectors = ['h1', '.product-title', '[data-testid*="title"]']
                    product_name = ""
                    
                    for selector in title_selectors:
                        try:
                            title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                            product_name = title_element.text.strip()
                            break
                        except:
                            continue
                            
                    if product_name and 'lancome' in product_name.lower():
                        product = ProductInfo(
                            url=url,
                            name=product_name,
                            price="N/A",
                            rating="N/A",
                            review_count="N/A",
                            brand="Lancôme",
                            market=market
                        )
                        products.append(product)
                        
                except Exception as e:
                    self.logger.debug(f"Failed to extract product from {url}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error parsing products from source: {e}")
            
        return products
        
    def extract_product_info(self, element, market: str) -> Optional[ProductInfo]:
        """Extract product information from element"""
        try:
            # Try to find product URL
            url = ""
            if element.tag_name == 'a':
                url = element.get_attribute('href')
            else:
                link = element.find_element(By.TAG_NAME, 'a')
                url = link.get_attribute('href')
                
            if not url.startswith('http'):
                url = urljoin(self.get_tiktok_shop_url(market), url)
                
            # Extract product name
            name_selectors = ['.product-name', '.item-title', 'h3', 'h4']
            name = ""
            for selector in name_selectors:
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, selector)
                    name = name_element.text.strip()
                    break
                except:
                    continue
                    
            # Extract price
            price_selectors = ['.price', '.product-price', '.cost']
            price = "N/A"
            for selector in price_selectors:
                try:
                    price_element = element.find_element(By.CSS_SELECTOR, selector)
                    price = price_element.text.strip()
                    break
                except:
                    continue
                    
            # Extract rating and review count
            rating = "N/A"
            review_count = "N/A"
            
            try:
                rating_element = element.find_element(By.CSS_SELECTOR, '.rating, .star-rating')
                rating = rating_element.text.strip()
            except:
                pass
                
            try:
                review_element = element.find_element(By.CSS_SELECTOR, '.review-count, .reviews')
                review_count = review_element.text.strip()
            except:
                pass
                
            return ProductInfo(
                url=url,
                name=name,
                price=price,
                rating=rating,
                review_count=review_count,
                brand="Lancôme",
                market=market
            )
            
        except Exception as e:
            self.logger.debug(f"Failed to extract product info: {e}")
            return None
            
    def scrape_product_reviews(self, product: ProductInfo) -> List[ReviewInfo]:
        """Scrape reviews for a specific product"""
        self.logger.info(f"Scraping reviews for: {product.name}")
        
        reviews = []
        self.driver = self.setup_driver(product.market)
        
        try:
            self.driver.get(product.url)
            self.random_delay(3, 5)
            
            # Try to find reviews section
            review_selectors = [
                '.reviews-section',
                '.review-list',
                '[data-testid*="review"]',
                '.comment-section'
            ]
            
            review_section = None
            for selector in review_selectors:
                try:
                    review_section = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
                    
            if not review_section:
                self.logger.warning(f"No review section found for {product.url}")
                return []
                
            # Scroll to load more reviews
            self.scroll_to_load_reviews()
            
            # Extract individual reviews
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, '.review-item, .comment-item, .feedback-item')
            
            for element in review_elements:
                review = self.extract_review_info(element, product)
                if review:
                    reviews.append(review)
                    
        except Exception as e:
            self.logger.error(f"Error scraping reviews for {product.url}: {e}")
            
        finally:
            if self.driver:
                self.driver.quit()
                
        return reviews
        
    def scroll_to_load_reviews(self):
        """Scroll page to trigger loading of more reviews"""
        try:
            # Scroll down multiple times to load more content
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay(2, 3)
                
            # Try to click "Load More" buttons if they exist
            load_more_selectors = [
                '.load-more',
                '.show-more',
                'button[data-testid*="load"]'
            ]
            
            for selector in load_more_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        self.random_delay(2, 3)
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Error during scroll/load more: {e}")
            
    def extract_review_info(self, element, product: ProductInfo) -> Optional[ReviewInfo]:
        """Extract review information from element"""
        try:
            # Extract reviewer name
            reviewer_name = "Anonymous"
            name_selectors = ['.reviewer-name', '.username', '.author']
            for selector in name_selectors:
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, selector)
                    reviewer_name = name_element.text.strip()
                    break
                except:
                    continue
                    
            # Extract rating
            rating = "N/A"
            rating_selectors = ['.rating', '.star-rating', '.score']
            for selector in rating_selectors:
                try:
                    rating_element = element.find_element(By.CSS_SELECTOR, selector)
                    rating = rating_element.get_attribute('data-rating') or rating_element.text.strip()
                    break
                except:
                    continue
                    
            # Extract review text
            review_text = ""
            text_selectors = ['.review-text', '.comment-text', '.content']
            for selector in text_selectors:
                try:
                    text_element = element.find_element(By.CSS_SELECTOR, selector)
                    review_text = text_element.text.strip()
                    break
                except:
                    continue
                    
            # Extract date
            review_date = "N/A"
            date_selectors = ['.review-date', '.timestamp', '.date']
            for selector in date_selectors:
                try:
                    date_element = element.find_element(By.CSS_SELECTOR, selector)
                    review_date = date_element.text.strip()
                    break
                except:
                    continue
                    
            # Extract helpful votes
            helpful_votes = "0"
            helpful_selectors = ['.helpful-count', '.likes', '.thumbs-up']
            for selector in helpful_selectors:
                try:
                    helpful_element = element.find_element(By.CSS_SELECTOR, selector)
                    helpful_votes = helpful_element.text.strip()
                    break
                except:
                    continue
                    
            # Generate review ID
            review_id = f"{hash(reviewer_name + review_text + review_date) % 1000000}"
            
            return ReviewInfo(
                product_url=product.url,
                product_name=product.name,
                reviewer_name=reviewer_name,
                rating=rating,
                review_text=review_text,
                review_date=review_date,
                verified_purchase="N/A",
                helpful_votes=helpful_votes,
                review_id=review_id,
                country_market=product.market,
                scrape_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.debug(f"Failed to extract review info: {e}")
            return None
            
    def save_to_csv(self, reviews: List[ReviewInfo], filename: str):
        """Save reviews to CSV file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'product_url', 'product_name', 'reviewer_name', 'rating',
                    'review_text', 'review_date', 'verified_purchase',
                    'helpful_votes', 'review_id', 'country_market', 'scrape_timestamp'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for review in reviews:
                    writer.writerow(asdict(review))
                    
            self.logger.info(f"Saved {len(reviews)} reviews to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
            
    def run_complete_scraping(self) -> List[ReviewInfo]:
        """Run complete scraping process for both markets"""
        all_reviews = []
        
        for market in ['vietnam', 'saudi_arabia']:
            try:
                self.logger.info(f"Starting scraping for {market}")
                
                # Step 1: Find Lancôme products
                products = self.search_lancome_products(market)
                self.logger.info(f"Found {len(products)} Lancôme products in {market}")
                
                # Step 2: Scrape reviews for each product
                for product in products:
                    reviews = self.scrape_product_reviews(product)
                    all_reviews.extend(reviews)
                    self.logger.info(f"Collected {len(reviews)} reviews for {product.name}")
                    
                    # Add delay between products
                    self.random_delay(5, 10)
                    
            except Exception as e:
                self.logger.error(f"Error scraping {market}: {e}")
                
        return all_reviews


def main():
    """Main execution function"""
    scraper = TikTokShopScraper(headless=False)  # Set to True for production
    
    try:
        # Run complete scraping
        reviews = scraper.run_complete_scraping()
        
        # Save results
        if reviews:
            filename = "aymane_aallaoui_tiktok_shop_reviews_sample.csv"
            scraper.save_to_csv(reviews, filename)
            print(f"\nScraping completed! Found {len(reviews)} reviews total.")
            print(f"Results saved to {filename}")
        else:
            print("No reviews found. This might be due to:")
            print("- TikTok Shop not available in target markets")
            print("- Lancôme products not available")
            print("- Anti-bot protection blocking access")
            print("- Changes in website structure")
            
    except Exception as e:
        print(f"Error during execution: {e}")
        

if __name__ == "__main__":
    main()
