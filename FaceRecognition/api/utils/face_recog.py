import requests

TF_URL = "http://172.20.53.10:4567/api/analyze"


def get_embeddings(img_path):
    url = TF_URL
    files = {"image": open(img_path, "rb")}
    response = requests.post(url, files=files)
    json_data = response.json()
    return json_data
