from scraping import save_page_source
import json
import pandas as pd

# Load product links from JSON file
with open('product_links.json', 'r') as file:
    data = json.load(file)

product_data = []

# Scrape data for each product link
for link in data['product_links']:
    page_source = save_page_source(f"https://www.brilliantearth.com/{link}")
    product_data.append({'link': link, 'data': page_source}) 

# Debugging: Print extracted data before saving
for item in product_data:
    print(f"Link: {item['link']}")
    print(f"Product Name: {item['data'].get('Product Name', 'N/A')}")
    print(f"Image Links: {item['data'].get('Image Links', [])}")
    print(f"Video Links: {item['data'].get('Video Links', [])}")
    print("-" * 50)

# Extract product names, image links, and video links safely
df = pd.DataFrame([
    {
        "Link": item["link"],
        "Product Name": item["data"].get("Product Name", "N/A"),
        "Image Links": ", ".join(item["data"].get("Image Links", [])),  # Convert list to string safely
        "Video Link": ", ".join(item["data"].get("Video Links", []))  # Convert list to string safely
    }
    for item in product_data
])

# Save to Excel
df.to_excel("product_data.xlsx", index=False)
print("Excel file saved successfully!")
