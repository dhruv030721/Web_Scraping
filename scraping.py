import os
import requests
import multiprocessing
from playwright.sync_api import sync_playwright

# Create base directory for saving media
BASE_FOLDER = "wedding_ring_women"
os.makedirs(BASE_FOLDER, exist_ok=True)


def download_file(url, folder):
    """Download image/video from URL into the specified folder."""
    filename = url.split("/")[-1].split("?")[0]  # Extract filename
    filepath = os.path.join(folder, filename)

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download: {url}")


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


def scrape_product_images(page, product_folder):
    """Download all images within the id-carousel-thumb div for the given product."""
    images = page.locator("#id-carousel-thumb img").evaluate_all("elements => elements.map(e => e.src)")
    for img_url in images:
        if img_url.startswith("http"):
            download_file(img_url, product_folder)


def process_product_variations(page, product_folder):
    """Click center stone and color options, downloading images for each combination."""
    stone_elements = page.locator("a.center_stone_img:visible")
    stone_count = stone_elements.count()

    if stone_count == 0:
        process_color_variations(page, product_folder)
        return

    for i in range(stone_count):
        try:
            stone_elements.nth(i).wait_for(state="visible", timeout=5000)
            stone_elements.nth(i).click()
            page.wait_for_timeout(3000)
            process_color_variations(page, product_folder)
        except Exception as e:
            print(f"Skipping Center Stone {i+1} due to error: {e}")


def process_color_variations(page, product_folder):
    """Click color options and download images for each."""
    color_elements = page.locator("a.change_track_info")
    color_count = color_elements.count()

    if color_count == 0:
        scrape_product_images(page, product_folder)
        return

    for j in range(color_count):
        try:
            color_elements.nth(j).click()
            page.wait_for_timeout(2000)
            scrape_product_images(page, product_folder)
        except Exception as e:
            print(f"Skipping Color {j+1} due to error: {e}")


def scrape_product(link):
    """Scrape a single product page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Use headless=True for silent execution
        page = browser.new_page()

        try:
            print(f"Opening: {link}")
            page.goto(link, timeout=60000)

            # Extract product name for folder creation
            product_name = page.locator("h1").inner_text().strip().replace(" ", "_")
            product_folder = os.path.join(BASE_FOLDER, product_name)
            os.makedirs(product_folder, exist_ok=True)

            # Process variations and download images
            process_product_variations(page, product_folder)

        except Exception as e:
            print(f"Error scraping {link}: {e}")

        browser.close()


def main():
    """Main function to scrape all product links in parallel."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.brilliantearth.com/wedding-rings/womens/")

        # Load more products by scrolling
        scroll_and_load_more(page)

        # Get all product links
        product_links = page.locator("a.pdp_url").evaluate_all("elements => elements.map(e => e.href)")
        print(f"Found {len(product_links)} products.")

        browser.close()

    # Define number of processes (CPU cores or custom value)
    num_processes = min(4, len(product_links))  # Use 4 processes or fewer if links are less

    # Use multiprocessing to scrape products in parallel
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(scrape_product, product_links)  

if __name__ == "__main__":
    main()
