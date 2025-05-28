import os
import pandas as pd
import multiprocessing
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

# Create base directory for saving Excel
BASE_FOLDER = "wedding_ring_women"
os.makedirs(BASE_FOLDER, exist_ok=True)

# Define Excel file path
EXCEL_FILE = os.path.join(BASE_FOLDER, "wedding_rings_data.xlsx")

def ensure_excel_file():
    """Ensure the Excel file exists with headers."""
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=["Link", "Product Name", "Product Details", "Iframe Link"])
        df.to_excel(EXCEL_FILE, index=False)
        print("Created a new Excel file.")

def expand_dropdown(page):
    try:
        dropdown = page.locator("span.title_shape + svg")
        if dropdown.is_visible():
            print("Expanding the dropdown...")
            dropdown.click()
            page.wait_for_timeout(1000)
        else:
            print("Dropdown not visible, skipping...")
    except Exception as e:
        print(f"Failed to expand dropdown: {e}")

def scroll_and_load_more(page):
    """Scroll down and wait for new products to load."""
    prev_height = 0
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)  # Wait for loading
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == prev_height:
            break
        prev_height = new_height

def save_to_excel(product_info):
    """Append product info to Excel file."""
    if product_info:
        # Load existing Excel file
        existing_df = pd.read_excel(EXCEL_FILE)

        # Append new product data
        new_df = pd.DataFrame([product_info])
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)

        # Save to Excel
        updated_df.to_excel(EXCEL_FILE, index=False)
        print(f"Added product: {product_info['Link']}")

def scrape_product_variations(page, link):
    """Scrape all color and shape combinations for a product."""
    product_data = []

    # Get the list of color elements
    color_elements = page.locator("a.change_track_info")
    color_count = color_elements.count()

    # If no colors are available, scrape shapes directly
    if color_count == 0:
        print("No colors found, scraping shapes directly...")
        data = scrape_shapes_for_color(page, link)
        if data:
            product_data.extend(data)
        return product_data

    # Iterate over each color
    for color_index in range(color_count):
        try:
            # Click the current color
            color_elements = page.locator("a.change_track_info")
            color_elements.nth(color_index).scroll_into_view_if_needed()
            color_elements.nth(color_index).click()
            page.wait_for_timeout(2000)

            # Expand the shape dropdown once per color change
            expand_dropdown(page)

            # Scrape all shapes for the selected color
            print(f"Processing Color {color_index+1}...")
            data = scrape_shapes_for_color(page, link)
            if data:
                product_data.extend(data)

        except Exception as e:
            print(f"Skipping Color {color_index+1} due to error: {e}")

    return product_data



def scrape_shapes_for_color(page, link):
    """Scrape all shapes for the currently selected color."""
    product_data = []

    # Get the list of stone elements
    stone_elements = page.locator(".diamondshapeselect-item a")
    stone_count = stone_elements.count()

    # If no shapes are available, scrape the product directly
    if stone_count == 0:
        data = scrape_product_data(page, link)
        if data:
            product_data.append(data)
        return product_data

    # Iterate over each shape
    for shape_index in range(stone_count):
        try:
            # Re-fetch stone elements in case of DOM changes
            stone_elements = page.locator(".diamondshapeselect-item a")
            stone_elements.nth(shape_index).scroll_into_view_if_needed()
            stone_elements.nth(shape_index).click()
            page.wait_for_timeout(2000)

            # Scrape product data for this color-shape combination
            data = scrape_product_data(page, link)
            if data:
                product_data.append(data)

        except Exception as e:
            print(f"Skipping Shape {shape_index+1} due to error: {e}")

    return product_data



def scrape_product_data(page, link):
    """Scrape product details from the current page state."""
    try:
        # Get HTML content and parse with BeautifulSoup
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Extract product name
        product_name_tag = soup.find("h1", class_="heading")
        product_name = product_name_tag.text.strip() if product_name_tag else "N/A"

        # Extract product details
        product_detail = ""
        ring_info_ul = soup.find('ul', class_='tm-space-y-2 tm-list-none tm-pl-0')
        if ring_info_ul:
            ring_data = [
                re.sub(r'\s+', ' ', li.get_text().strip()).strip()
                for li in ring_info_ul.find_all('li')
            ]
            product_detail = ', '.join(ring_data)

        # Extract iframe link
        thumb_video_div = soup.find("div", id="thumb-video")
        iframe_src = "N/A"
        if thumb_video_div:
            iframe_tag = thumb_video_div.find("iframe")
            if iframe_tag and iframe_tag.has_attr("src"):
                iframe_src = iframe_tag["src"].lstrip("//")

        # Prepare product data
        product_info = {
            "Link": link,
            "Product Name": product_name,
            "Product Details": product_detail,
            "Iframe Link": iframe_src
        }

        print(f"Scraped data: {product_info}")
        return product_info

    except Exception as e:
        print(f"Error scraping data for {link}: {e}")
        return None


def scrape_product(link):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
        )
        page = context.new_page()

        try:
            print(f"Opening: {link}")
            page.goto(link, timeout=60000)
            product_data = scrape_product_variations(page, link)
            for product_info in product_data:
                save_to_excel(product_info)
        except Exception as e:
            print(f"Error scraping {link}: {e}")
        finally:
            context.close()
            browser.close()


def main():
    """Main function to scrape all product links in parallel."""
    # Ensure Excel file exists
    ensure_excel_file()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }
        )
        page = context.new_page()

        page.goto("https://www.brilliantearth.com/engagement-rings/solitaire/")

        # Load more products by scrolling
        scroll_and_load_more(page)

        # Get all product links
        product_links = page.locator("a.pdp_url").evaluate_all("elements => elements.map(e => e.href)")
        print(f"Found {len(product_links)} products.")

        browser.close()

    # Use multiprocessing to scrape products in parallel
    with multiprocessing.Pool(processes=1) as pool:
        pool.map(scrape_product, product_links)


if __name__ == "__main__":
    main()
