import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Open and read the saved HTML file
with open("products.html", "r", encoding="utf-8") as file:
    html = file.read()

# Parse with BeautifulSoup
soup = BeautifulSoup(html, "html.parser")

# Extract product links
product_names = soup.find_all("a", class_="clk_through")
product_links = set()  # Using a set to avoid duplicates

# Normalize URLs
for product in product_names:
    if product.has_attr('href'):
        url = product['href']
        parsed_url = urlparse(url)
        clean_url = parsed_url.path.rstrip("/")  # Remove trailing slash and query parameters
        product_links.add(clean_url)

# Convert set back to a list
unique_product_links = list(product_links)

print(len(unique_product_links))

# Save to JSON file
with open("product_links.json", "w", encoding="utf-8") as json_file:
    json.dump({"product_links": unique_product_links}, json_file, indent=4)

print("Unique and cleaned product links saved to 'product_links.json'.")
