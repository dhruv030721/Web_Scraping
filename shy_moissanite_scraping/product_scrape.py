import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
from urllib.parse import urlparse, urljoin
import time

def create_product_folder(product_title):
    """Create a folder with the product title"""
    folder_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in product_title)
    folder_path = os.path.join('products', folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def fix_url(url):
    """Add https scheme to protocol-relative URLs"""
    if url.startswith('//'):
        return f'https:{url}'
    elif url.startswith('/'):
        return f'https://www.shymoissanite.com{url}'
    return url

def download_file(url, folder_path, file_name):
    """Download a file from URL and save it to the specified folder"""
    try:
        # Fix the URL if it's protocol-relative
        fixed_url = fix_url(url)
        # Remove any query parameters from the URL
        clean_url = fixed_url.split('?')[0]
        print(f"Downloading from: {clean_url}")
        
        response = requests.get(fixed_url, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Successfully downloaded: {file_name}")
            return True
        else:
            print(f"Failed to download {fixed_url}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
    return False

def scrape_product(url):
    # Create main products directory if it doesn't exist
    os.makedirs('products', exist_ok=True)
    
    # Send a GET request to the URL
    response = requests.get(url)
    product_information = {}
    
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get Product Title
        product_title_div = soup.find('div', class_='product__title')
        product_title_h1 = product_title_div.find('h1')
        product_information['Title'] = product_title_h1.text.strip()
        
        # Create folder for this product
        folder_path = create_product_folder(product_information['Title'])
        product_information['Folder'] = folder_path
        
        # Get Product Price
        product_money_span = soup.find('span', class_="price-item")
        product_money_tag = product_money_span.find('span')
        product_information['Price'] = product_money_tag.text.strip()
        
        # Get Product Cut and Size
        # product_detail_tr = soup.find_all('tr')
        # product_detail_cut = product_detail_tr[1].find_all('td')
        # product_detail_size = product_detail_tr[3].find_all('td')
        # product_information['Cut'] = product_detail_cut[1].text.strip()
        # product_information['Size'] = product_detail_size[1].text.replace('\xa0', ' ').strip()
        
        # Get and Download Product Media
        product_media_tags = soup.find_all('li', class_='grid__item')
        image_count = 0
        video_count = 0
        
        for media_tag in product_media_tags:
            # Handle Videos
            video_sources = media_tag.find_all('source')
            for video_tag in video_sources:
                if 'src' in video_tag.attrs:
                    video_url = video_tag['src']
                    if 'thumbnail' not in video_url.lower():  # Skip video thumbnails
                        video_count += 1
                        file_ext = os.path.splitext(urlparse(video_url).path)[1] or '.mp4'
                        file_name = f"video_{video_count}{file_ext}"
                        download_file(video_url, folder_path, file_name)
            
            # Handle Images
            img_tag = media_tag.find('img')
            if img_tag and 'src' in img_tag.attrs:
                img_url = img_tag['src']
                # Skip thumbnails and preview images
                if not any(skip in img_url.lower() for skip in ['tiny', 'thumbnail', 'preview']):
                    image_count += 1
                    file_ext = os.path.splitext(urlparse(img_url).path)[1] or '.jpg'
                    file_name = f"image_{image_count}{file_ext}"
                    download_file(img_url, folder_path, file_name)
        
        # Add media counts to product information
        product_information['Images'] = image_count
        product_information['Videos'] = video_count
        product_information['URL'] = url
        
        # Save to Excel
        df = pd.DataFrame([product_information])
        excel_path = 'product_data.xlsx'
        
        # If Excel file exists, append to it; otherwise create new
        if os.path.exists(excel_path):
            existing_df = pd.read_excel(excel_path)
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_excel(excel_path, index=False)
        else:
            df.to_excel(excel_path, index=False)
        
        print(f"\nProduct information saved to {excel_path}")
        print(f"Media files saved to {folder_path}")
        print(f"Summary:")
        print(f"Images downloaded: {image_count}")
        print(f"Videos downloaded: {video_count}")
        
        return product_information
    
    else:
        print(f"Failed to fetch the URL. Status code: {response.status_code}")
        return None

# Example usage
if __name__ == "__main__":
    url = "https://www.shymoissanite.com/products/marquise-round-moissanite-eternity-band"
    product_info = scrape_product(url)