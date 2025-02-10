import requests
import json

url = "http://127.0.0.1:8060/app/embed-pickle"
files = {"file": open("documents.pkl", "rb")}

with requests.post(url, files=files, stream=True) as response:
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            print(f"📄 Text: {data['text']}")
            print(f"🔢 Embedding (384-dim, 일부만 표시):")

            embedding = data['embedding']

            # ✅ 앞부분 4개, 뒷부분 4개만 표시
            preview = embedding[:4] + ["..."] + embedding[-4:]
            print(preview)

            print("-" * 50)
