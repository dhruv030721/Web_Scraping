import re
import json

# Read the content from the text file
with open("products.txt", "r", encoding="utf-8") as file:
    text = file.read()

# Normalize the text (replace escaped newlines if necessary)
text = text.replace("\\n", "\n").replace("\\r", "\r").replace("\\\"", "\"")

# Regular expression to match URLs in "url": "https://www.brilliantearth.com/..."
pattern = r'"url":\s*"(?P<url>https://www\.brilliantearth\.com/[^"]+)"'

# Find all matching URLs
matches = re.findall(pattern, text)

# Save the extracted links to a JSON file
with open("links.json", "w", encoding="utf-8") as json_file:
    json.dump(matches, json_file, indent=4)

print(f"Extracted {len(matches)} links and saved to links.json")
