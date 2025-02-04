from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
import logging
from typing import List
import pandas as pd
from scraping import scrape_single_product

class ThreadedProductScraper:
    def __init__(self, max_threads: int = 3):
        """
        Initialize the threaded scraper
        
        Args:
            max_threads (int): Maximum number of concurrent threads to use
        """
        self.max_threads = max_threads
        self.queue = Queue()
        self.results = []
        self.lock = threading.Lock()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(threadName)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def worker(self):
        """Worker function that processes URLs from the queue"""
        while True:
            try:
                # Get URL from queue with timeout
                url = self.queue.get(timeout=3)
                self.logger.info(f"Processing URL: {url}")
                
                try:
                    # Call the existing scrape_single_product function
                    scrape_single_product(url)
                    self.logger.info(f"Completed processing URL: {url}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing URL {url}: {str(e)}")
                
                finally:
                    self.queue.task_done()
                    
            except Queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"Worker thread error: {str(e)}")
                break

    def process_urls(self, urls: List[str]) -> None:
        """
        Process multiple URLs in parallel
        
        Args:
            urls: List of URLs to process
        """
        # Add URLs to queue
        for url in urls:
            self.queue.put(url)

        # Create and start worker threads
        threads = []
        for _ in range(min(self.max_threads, len(urls))):
            thread = threading.Thread(target=self.worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Wait for all URLs to be processed
        self.queue.join()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Combine Excel files if needed
        self.combine_excel_files()

    def combine_excel_files(self):
        """Combine individual Excel files into a single file if needed"""
        try:
            df = pd.read_excel('product_data.xlsx')
            df.to_excel('combined_product_data.xlsx', index=False)
            self.logger.info("Successfully combined data into combined_product_data.xlsx")
        except Exception as e:
            self.logger.error(f"Error combining Excel files: {str(e)}")

if __name__ == "__main__":
    # List of collection URLs to scrape
    urls = [
        "https://www.shymoissanite.com/collections/bridal?page=1",
        "https://www.shymoissanite.com/collections/bridal?page=2",
        # Add more pages as needed
    ]
    
    # Create scraper instance with 3 threads
    scraper = ThreadedProductScraper(max_threads=3)
    
    # Start scraping
    print(f"Starting to scrape {len(urls)} pages with {scraper.max_threads} threads...")
    scraper.process_urls(urls)
    print("Scraping completed!")