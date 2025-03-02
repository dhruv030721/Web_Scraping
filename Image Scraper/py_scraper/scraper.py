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
            
    # Prepare product data
    iframe_link = iframe_src
    if isinstance(iframe_link, str):  # Ensure it's a string before modification
        iframe_link = iframe_link.lstrip("//")
            
    
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
        "Image Links": ", ".join(img_links),  # Convert list to string safely
        "Iframe Link": iframe_link
    }
    
    print({ "Link": data.url,
        "Product Name": product_name,
        "Image Links": ", ".join(img_links),  # Convert list to string safely
        "Iframe Link": iframe_link})

    # Append new product data
    new_df = pd.DataFrame([product_info])
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)

    # Save the updated DataFrame to the Excel file
    updated_df.to_excel(excel_file, index=False)
    print(f"Added product: {data.url}")

    
    return True

# Run the app if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)
