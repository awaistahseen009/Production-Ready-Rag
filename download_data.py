import os
import requests
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET

# Create directory
folder = "data/papers"
os.makedirs(folder, exist_ok=True)

topics = [
    # "machine learning",
    "computer vision",
    "YOLO object detection",
    "large language models",
    "retrieval augmented generation"
]

base_url = "http://export.arxiv.org/api/query?search_query="

count = 0
max_papers = 100

def clean_filename(text):
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = text.replace("\n", " ").strip()
    return text[:150]  # limit filename length

for topic in topics:
    query = quote(topic)
    url = f"{base_url}{query}&start=0&max_results=15"
    response = requests.get(url)

    root = ET.fromstring(response.text)

    ns = {"atom": "http://www.w3.org/2005/Atom"}

    for entry in root.findall("atom:entry", ns):
        if count >= max_papers:
            break

        arxiv_id = entry.find("atom:id", ns).text.split("/")[-1]
        title = entry.find("atom:title", ns).text

        clean_title = clean_filename(title)
        filename = f"{folder}/{clean_title}.pdf"
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        try:
            r = requests.get(pdf_url)
            if r.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(r.content)
                print(f"Downloaded: {clean_title}")
                count += 1
        except Exception as e:
            print("Failed:", pdf_url, e)

    if count >= max_papers:
        break

print(f"\n✅ Total downloaded: {count}")
