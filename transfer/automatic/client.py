import os
import time
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.normpath(os.path.join(SCRIPT_DIR, "recordings"))
SERVER_IP = '192.168.200.193'
URL = f'http://{SERVER_IP}:5000/upload'

print(f"Monitoring folder: {FOLDER}")

while True:
    files = os.listdir(FOLDER)
    for filename in files:
        path = os.path.join(FOLDER, filename)
        if os.path.isfile(path) and filename.startswith("rec_"):
            with open(path, 'rb') as f:
                requests.post(URL, files={'file': f})
            os.remove(path)
    time.sleep(0.1)
