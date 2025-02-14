from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def setup_driver():
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium-browser"  # Use Chromium
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--start-maximized')  # Open in full screen
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # Bypass bot detection
    chrome_options.add_argument('--disable-gpu')

    service = Service('/usr/bin/chromedriver')  # Use manually installed chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver

def get_page_source(url):
    driver = setup_driver()
    driver.get(url)

    # Wait for full page load
    driver.implicitly_wait(10)

    # Get page HTML
    html = driver.page_source
    driver.quit()

    return html

# Test
url = "https://www.brilliantearth.com/Callista-Diamond-Ring-Rose-Gold-BE1D3975-17564638/"
html_content = get_page_source(url)

with open("output.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("HTML saved successfully.")

