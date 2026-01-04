import requests
import os
from dotenv import load_dotenv
load_dotenv(override=True)
url = os.getenv("MODAL_RERANKER_URL")

data = {
    "query": "What is YOLO-World and how does it work?",
    "documents": [
        "YOLO-World is a real-time open-vocabulary object detector that can detect any object given text prompts.",
        "Cats are cute animals that like to sleep a lot.",
        "YOLOv8 is the latest version from Ultralytics with improved speed and accuracy.",
        "Open-vocabulary detection allows models to recognize objects beyond fixed categories.",
        "Transformers are a type of neural network architecture used in NLP."
    ]
}

response = requests.post(url, json=data)
print(response.json())