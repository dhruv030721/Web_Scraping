from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import os
import requests
import pandas as pd
import time
from urllib.parse import urlparse

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    return driver

def create_product_folder(product_title):
    folder_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in product_title)
    folder_path = os.path.join('products', folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def download_file(url, folder_path, file_name):
    try:
        # Remove any query parameters from the URL
        clean_url = url.split('?')[0]
        response = requests.get(clean_url, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Successfully downloaded: {file_name}")
            return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
    return False

def get_table_data(driver):
    try:
        time.sleep(2)  # Wait for table to load
        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
        cut = ""
        size = ""
        
        if len(rows) > 1:
            cut_cells = rows[1].find_elements(By.TAG_NAME, "td")
            if len(cut_cells) > 0:
                cut = cut_cells[1].text.strip()
        
        if len(rows) > 3:
            size_cells = rows[3].find_elements(By.TAG_NAME, "td")
            if len(size_cells) > 0:
                size = size_cells[1].text.strip()
                
        return cut, size
    except Exception as e:
        print(f"Error extracting table data: {str(e)}")
        return "", ""

def wait_for_element(driver, by, value, timeout=10, retries=3):
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except (TimeoutException, StaleElementReferenceException) as e:
            if attempt == retries - 1:
                print(f"Failed to find element {value} after {retries} attempts")
                raise e
            time.sleep(2)
    return None

def download_product_media(driver, folder_path):
    """Function to download media from thumbnail-list structure"""
    media_count = {'images': 0, 'videos': 0}
    
    try:
        # Wait for page to load
        time.sleep(2)
        
        # Find the thumbnail-list container
        thumbnail_list = wait_for_element(driver, By.CLASS_NAME, "thumbnail-list")
        if not thumbnail_list:
            print("Thumbnail list not found")
            return media_count
            
        # Find all li elements within the thumbnail list
        thumbnails = thumbnail_list.find_elements(By.TAG_NAME, "li")
        print(f"Found {len(thumbnails)} thumbnails")
        
        for index, thumbnail in enumerate(thumbnails, 1):
            try:
                print(f"\nProcessing thumbnail {index}")
                
                # Check for deferred media (videos)
                deferred_media = thumbnail.find_elements(By.CLASS_NAME, "deferred-media")
                if deferred_media:
                    for media in deferred_media:
                        try:
                            # Click to load the video
                            button = media.find_element(By.CLASS_NAME, "deferred-media__poster")
                            if button.is_displayed() and button.is_enabled():
                                button.click()
                                time.sleep(2)  # Wait for video to load
                            
                            # Look for video element
                            video = media.find_element(By.TAG_NAME, "video")
                            video_url = video.get_attribute("src")
                            
                            # If no direct src, check source tags
                            if not video_url:
                                sources = video.find_elements(By.TAG_NAME, "source")
                                for source in sources:
                                    video_url = source.get_attribute("src")
                                    if video_url:
                                        break
                            
                            if video_url and video_url.strip():
                                print(f"Found video URL: {video_url}")
                                media_count['videos'] += 1
                                file_name = f"video_{media_count['videos']}{os.path.splitext(urlparse(video_url).path)[1]}"
                                if download_file(video_url, folder_path, file_name):
                                    print(f"Successfully downloaded video {media_count['videos']}")
                                    
                        except Exception as e:
                            print(f"Error processing video in thumbnail {index}: {str(e)}")
                
                # Check for images
                images = thumbnail.find_elements(By.TAG_NAME, "img")
                for img in images:
                    try:
                        img_url = img.get_attribute("src")
                        if img_url:
                            img_url = img_url.split('?')[0]  # Remove query parameters
                            # Skip if it's a tiny thumbnail
                            if 'tiny' not in img_url.lower():
                                media_count['images'] += 1
                                file_name = f"image_{media_count['images']}{os.path.splitext(urlparse(img_url).path)[1]}"
                                if download_file(img_url, folder_path, file_name):
                                    print(f"Successfully downloaded image {media_count['images']}")
                    
                    except Exception as e:
                        print(f"Error processing image in thumbnail {index}: {str(e)}")
            
            except Exception as e:
                print(f"Error processing thumbnail {index}: {str(e)}")
                continue
        
        print(f"\nMedia download summary:")
        print(f"Images downloaded: {media_count['images']}")
        print(f"Videos downloaded: {media_count['videos']}")
        
    except Exception as e:
        print(f"Error in media download process: {str(e)}")
    
    return media_count
def scrape_single_product(url):
    driver = setup_driver()
    os.makedirs('products', exist_ok=True)
    product_data = []
    
    try:
        print(f"Accessing URL: {url}")
        driver.get(url)
        time.sleep(5)
        
        try:
            # Find all product links
            product_links = wait_for_element(driver, By.CLASS_NAME, "grid__item", timeout=15)
            product_links = driver.find_elements(By.CSS_SELECTOR, "a.full-unstyled-link")
            print(f"Found {len(product_links)} product links")
            
            product_urls = set()
            for link in product_links:
                try:
                    url = link.get_attribute("href")
                    if url:
                        product_urls.add(url)
                except StaleElementReferenceException:
                    continue
                    
            print(f"Found {len(product_urls)} unique products")
            
            for product_url in product_urls:
                try:
                    print(f"\nProcessing product: {product_url}")
                    driver.get(product_url)
                    time.sleep(3)
                    
                    # Get title
                    title_element = wait_for_element(driver, By.CSS_SELECTOR, "div.product__title h1")
                    title = title_element.text if title_element else "Title not found"
                    print(f"Title: {title}")
                    
                    # Get price
                    try:
                        price_element = wait_for_element(driver, By.CSS_SELECTOR, "span.money")
                        price = price_element.text if price_element else "Price not found"
                    except:
                        try:
                            price_element = wait_for_element(driver, By.CSS_SELECTOR, ".price-item--regular")
                            price = price_element.text if price_element else "Price not found"
                        except:
                            price = "Price not found"
                    print(f"Price: {price}")
                    
                    # Get cut and size
                    cut, size = get_table_data(driver)
                    print(f"Cut: {cut}, Size: {size}")
                    
                    if title != "Title not found":
                        # Create folder for this product
                        folder_path = create_product_folder(title)
                        
                        # Download all media using the unified function
                        media_count = download_product_media(driver, folder_path)
                        
                        # Save product data
                        product_info = {
                            'Title': title,
                            'Price': price,
                            'Cut': cut,
                            'Size': size,
                            'URL': product_url,
                            'Folder': folder_path,
                            'Images': media_count['images'],
                            'Videos': media_count['videos']
                        }
                        product_data.append(product_info)
                        print(f"Completed processing: {title}")
                    
                except Exception as e:
                    print(f"Error processing product {product_url}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error finding products: {str(e)}")
        
        # Save data to Excel
        if product_data:
            df = pd.DataFrame(product_data)
            df.to_excel('product_data.xlsx', index=False)
            print("\nData saved to product_data.xlsx")
        else:
            print("No product data was collected")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    product_url = "https://www.shymoissanite.com/collections/bridal?page=1"
    scrape_single_product(product_url)