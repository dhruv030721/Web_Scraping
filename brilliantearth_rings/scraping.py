import os
import tempfile
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


def setup_driver1():
    chrome_options = Options()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    service = Service('/usr/bin/chromedriver')

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    
    return driver

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # Remove this for debugging

    # Use Chromium instead of Google Chrome
    chrome_options.binary_location = "/usr/bin/chromium-browser"

    # Manually specify ChromeDriver path for ARM64
    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def save_page_source(url):
    """ Fetches the webpage using Selenium and saves the HTML source. """
    driver = setup_driver()
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Page loaded successfully.")
    except TimeoutException:
        print("Page took too long to load.")
    
    # Get full page source
    html = driver.page_source
    
    # Save the page source
    with open("page_source.html", "w", encoding="utf-8") as file:
        file.write(html)

    print("Page source saved successfully.")
    
    driver.quit()
    data = extract_data()  # Process and save extracted data
    return data

def extract_data():
    """ Reads the saved HTML file and extracts product information. """
    with open("page_source.html", "r", encoding="utf-8") as file:
        html = file.read()

    # Parse with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Extract single product name
    product_name_tag = soup.find("h1", class_="heading")
    product_name = product_name_tag.text.strip() if product_name_tag else "N/A"

    # Extract image links
    img_divs = soup.find_all("div", class_="zoom-element")
    img_links = []
    
    video_divs = soup.find_all(lambda tag: tag.name == "video")
    video_links = []
    
    for video in video_divs:
        if video.has_attr("src"):
            video_links.append(video["src"])
    
    for div in img_divs:
        img_tags = div.find_all("img", class_="img-responsive")  
        for img in img_tags:
            if img.has_attr("src"):
                img_url = img["src"]
                if img_url.startswith("//image"):
                    img_links.append("https:" + img_url)  # Convert to absolute URL

    # Extract iframe src from #thumb-video
    thumb_video_div = soup.find("div", id="thumb-video")
    iframe_src = "N/A"

    if thumb_video_div:
        iframe_tag = thumb_video_div.find("iframe")
        if iframe_tag and iframe_tag.has_attr("src"):
            iframe_src = iframe_tag["src"]

    print({
        'Product Name': product_name,
        'Image Links': [", ".join(img_links)],
        'Iframe Link': iframe_src
    })

    return {
        'Product Name': product_name,
        'Image Links': [", ".join(img_links)],
        'Iframe Link': iframe_src
    }

# Run the functions in sequence
if __name__ == "__main__":
    url = "https://www.brilliantearth.com/Callista-Diamond-Ring-Rose-Gold-BE1D3975-17564638/"
    save_page_source(url)  # Fetch and save HTML
