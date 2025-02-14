import asyncio
import pyppeteer
from bs4 import BeautifulSoup

async def fetch_html(url):
    browser = await pyppeteer.launch(
        headless=True,
        executablePath="/usr/bin/chromium-browser",  # Use system Chromium
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage"
        ]
    )
    page = await browser.newPage()

    # Set a realistic User-Agent
    await page.setUserAgent("Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Go to the page and wait until fully loaded
    await page.goto(url, {"waitUntil": "networkidle2"}) 

    # Get page content
    html = await page.content()

    # Close browser
    await browser.close()
    
    return html

async def extract_data(url):
    html = await fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    product_name_tag = soup.find("h1", class_="heading")
    product_name = product_name_tag.text.strip() if product_name_tag else "N/A"

    img_links = [img["src"] for img in soup.find_all("img", class_="img-responsive") if img.has_attr("src")]
    iframe_src = soup.find("iframe")["src"] if soup.find("iframe") else "N/A"

    result = {
        "Product Name": product_name,
        "Image Links": img_links,
        "Iframe Link": iframe_src
    }
    
    print(result)
    return result

if __name__ == "__main__":
    url = "https://www.brilliantearth.com/Callista-Diamond-Ring-Rose-Gold-BE1D3975-17564638/"
    
    import nest_asyncio
    nest_asyncio.apply()  # Fixes "RuntimeError: Event loop is closed"

    loop = asyncio.get_event_loop()
    loop.run_until_complete(extract_data(url))
