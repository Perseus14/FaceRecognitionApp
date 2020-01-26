import requests

TF_URL = ''

def get_embeddings(img_path):
    url = TF_URL
    file = {'img_file' : open(img_path,'rb')}
    response = requests.post(url, files=file)
    return response