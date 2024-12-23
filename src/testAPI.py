import requests
import pandas as pd
import json

# URL中的路径参数: 
# - user_id = "12345"
# - action = "update"
url = "http://127.0.0.1:8000/process"
# ?currentTime=2024-11-10&language=en"
clientInfo = pd.read_json("./inputData/clientInfo.json")
clientInfo = clientInfo.to_dict('records')
clientInfo = json.dumps(clientInfo, ensure_ascii=False)

# currentTime = "2024-11-10"
# language = "en"

json_data = {
    "currentTime": "2024-11-10",
    "language": "en",
    "clientInfo": clientInfo
}

response = requests.post(url, json=json_data)
print(response.json())