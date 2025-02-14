import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Lock
from product_scrape import scrape_product

# Store the URLs to skip
SKIP_URLS = {
}

class ProductScraper:
    def __init__(self, num_workers=3):
        self.num_workers = num_workers
        self.successful = 0
        self.failed = 0
        self.lock = Lock()
        self.progress_bar = None
        self.failed_products = set()
        
    def increment_counters(self, success):
        with self.lock:
            if success:
                self.successful += 1
            else:
                self.failed += 1
            if self.progress_bar:
                self.progress_bar.update(1)

    def get_product_links_from_page(self, url):
        """Extract all product links from a single page"""
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                product_cards = soup.find_all('a', class_='full-unstyled-link')
                
                product_links = set()
                for card in product_cards:
                    if 'href' in card.attrs:
                        product_url = card['href']
                        full_url = urljoin('https://www.shymoissanite.com', product_url)
                        if full_url not in SKIP_URLS:  # Skip specified URLs
                            product_links.add(full_url)
                
                return product_links
            else:
                print(f"Failed to fetch page {url}. Status code: {response.status_code}")
                return set()
        except Exception as e:
            print(f"Error processing page {url}: {str(e)}")
            return set()

    def get_all_product_links(self, base_url, max_pages=None):
        """Get product links from all pages"""
        all_product_links = set()
        
        for page in range(1, 12):
            page_url = f"{base_url}?page={page}"
            print(f"\nProcessing page {page}...")
            
            page_links = self.get_product_links_from_page(page_url)
            
            if not page_links or (max_pages and page >= max_pages):
                break
                
            all_product_links.update(page_links)
            print(f"Found {len(page_links)} products on page {page}")
            print(f"Total products found so far: {len(all_product_links)}")
            
            time.sleep(1)
        
        return all_product_links

    def process_product(self, url):
        """Process a single product"""
        try:
            result = scrape_product(url)
            self.increment_counters(result)
            return result
        except Exception as e:
            print(f"\nError processing {url}: {str(e)}")
            self.increment_counters(False)
            self.failed_products.add(url)
            return False

    def process_all_products(self, product_links):
        """Process products using multiple threads"""
        print(f"\nStarting to process {len(product_links)} products with {self.num_workers} workers...")
        
        self.progress_bar = tqdm(total=len(product_links), desc="Processing products")
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all tasks to the executor
            future_to_url = {executor.submit(self.process_product, url): url 
                           for url in product_links}
            
            # Wait for all tasks to complete
            for future in future_to_url:
                try:
                    future.result()
                except Exception as e:
                    print(f"\nUnexpected error: {str(e)}")
        
        self.progress_bar.close()
        
        # Print summary
        print("\nProcessing completed!")
        print(f"Successfully processed: {self.successful} products")
        print(f"Failed to process: {self.failed} products")
        print(f"Failed to process: {self.failed_products} products")
        print(f"Total products attempted: {self.successful + self.failed}")

def main():
    # Create scraper instance with 3 worker threads
    scraper = ProductScraper(num_workers=3)
    
    # Base URL for the collection
    base_url = "https://www.shymoissanite.com/collections/bridal"
    
    # Get all product links
    print("Starting to collect product links...")
    product_links = scraper.get_all_product_links(base_url, max_pages=None)
    
    if product_links:
        print(f"\nFound {len(product_links)} unique product URLs (excluding skipped URLs)")
        user_input = input("Do you want to process all these products? (y/n): ")
        
        if user_input.lower() == 'y':
            scraper.process_all_products(product_links)
        else:
            print("Operation cancelled by user")
    else:
        print("No product links found")

if __name__ == "__main__":
    main()