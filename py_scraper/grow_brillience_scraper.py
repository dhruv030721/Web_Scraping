from fastapi import FastAPI
from pydantic import BaseModel
from bs4 import BeautifulSoup
import json
import pandas as pd
import os

# Initialize FastAPI app
app = FastAPI()

# Define request model
class ScrapeRequest(BaseModel):
    url: str

@app.get("/")
def home():
    return {"message": "Hello, FastAPI!"}

@app.post("/scrape")
def scrape(data: ScrapeRequest):

    print(data)
    
    with open("output.html", "r", encoding="utf-8") as file:
        html = file.read()

    # Parse with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Extract single product name
    product_name_div = soup.find("div", class_="pro-name")
    if product_name_div:
      product_name_tag = product_name_div.find("h1", class_="sub-hd")
      product_name = product_name_tag.text.strip() if product_name_tag else "N/A"
    else:
      product_name = "N/A"


    # Extract image links (all images with id="imageZoom")
    img_tags = soup.find_all("img", id="imageZoom")
    print(img_tags)
    
    img_links = []
    for img in img_tags:
        if img.has_attr("src"):
            img_url = img["src"]
            img_links.append(img_url)

    # Extract iframe src from #thumb-video (if needed)
    thumb_video_div = soup.find("div", id="thumb-video")

    # Define the Excel file name
    excel_file = "product_data.xlsx"

    # Ensure the Excel file exists; if not, create it with headers
    if not os.path.exists(excel_file):
        df = pd.DataFrame(columns=["Link", "Product Name", "Image Links", "Iframe Link"])
        df.to_excel(excel_file, index=False)
        print("Created a new Excel file.")
        
    # Load existing Excel file to append new data
    existing_df = pd.read_excel(excel_file)
    
    product_info = {
        "Link": data.url,
        "Product Name": product_name,
        "Image Links": ", ".join(img_links),  # Convert list to a string safely
    }
    
    print({
        "Link": data.url,
        "Product Name": product_name,
        "Image Links": ", ".join(img_links),
    })

    # Append new product data
    new_df = pd.DataFrame([product_info])
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Save the updated DataFrame to the Excel file
    updated_df.to_excel(excel_file, index=False)
    print(f"Added product: {data.url}")

    return {"success": True, "product": product_info}


# Run the app if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
