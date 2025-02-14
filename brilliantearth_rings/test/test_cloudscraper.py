import cloudscraper

def get_page_source(url):
    scraper = cloudscraper.create_scraper()
    html = scraper.get(url).text
    return html

url = "https://www.brilliantearth.com/Callista-Diamond-Ring-Rose-Gold-BE1D3975-17564638/"
html_content = get_page_source(url)

# Save HTML content
with open("output.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("HTML saved successfully.")

