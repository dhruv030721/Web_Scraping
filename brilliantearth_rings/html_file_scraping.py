import pandas as pd
from bs4 import BeautifulSoup

# Open and read the saved HTML file
with open("page_source.html", "r", encoding="utf-8") as file:
    html = file.read()

# Parse with BeautifulSoup
soup = BeautifulSoup(html, "html.parser")

# Extract product names
product_names = soup.find_all("h1", class_="heading")

img_divs = soup.find_all("div", class_="zoom-element")

img_links = []

# Loop through each div and find all img tags inside it
for div in img_divs:
    img_tags = div.find_all("img", class_="img-responsive")  # Find all <img> tags inside the div
    for img in img_tags:
        if img.has_attr("src"):  # Check if the img tag has a 'src' attribute
            img_url = img["src"]
            if img_url.startswith("//image"):  # Ensure it starts with "//image"
                img_links.append(img_url)

# Save extracted image URLs to an Excel file
df = pd.DataFrame({"Image Links": img_links})  # Create a DataFrame
df.to_excel("image_links.xlsx", index=False, engine="openpyxl")  # Save as Excel file

print("Image links saved to 'image_links.xlsx'")
