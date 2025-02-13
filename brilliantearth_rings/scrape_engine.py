from scraping import save_page_source
import json
import pandas as pd
import os

# Load product links from JSON file
with open('extracted_links.json', 'r') as file:
    data = json.load(file)

excel_file = "product_data.xlsx"

# Ensure the Excel file exists; if not, create it with headers
if not os.path.exists(excel_file):
    df = pd.DataFrame(columns=["Link", "Product Name", "Image Links", "Iframe Link"])
    df.to_excel(excel_file, index=False)
    print("Created a new Excel file.")

# Process each product one by one
for link in data['product_links']:
    page_source = save_page_source(f"https://www.brilliantearth.com/{link}")

    # Prepare product data
    iframe_link = page_source.get("Iframe Link", "")
    if isinstance(iframe_link, str):  # Ensure it's a string before modification
        iframe_link = iframe_link.lstrip("//")

    product_info = {
        "Link": link,
        "Product Name": page_source.get("Product Name", "N/A"),
        "Image Links": ", ".join(page_source.get("Image Links", [])),  # Convert list to string safely
        "Iframe Link": iframe_link
    }

    # Load existing Excel file to append new data
    existing_df = pd.read_excel(excel_file)

    # Append new product data
    new_df = pd.DataFrame([product_info])
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Save the updated DataFrame to the Excel file
    updated_df.to_excel(excel_file, index=False)
    print(f"Added product: {link}")

print("All products saved successfully!")
