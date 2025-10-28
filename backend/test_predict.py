# backend/test_predict.py
import requests

url = "http://127.0.0.1:5000/predict"
img_path = "test_image.jpg"  # put a test retinal image here

with open(img_path, "rb") as f:
    files = {"image": f}
    r = requests.post(url, files=files)
    print("Status:", r.status_code)
    print("Response:", r.json())
