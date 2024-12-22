import requests
import pandas as pd

# URL中的路径参数: 
# - user_id = "12345"
# - action = "update"
url = "http://127.0.0.1:8000/process"

clientInfo = pd.read_json("./inputData/clientInfo.json")

# JSON数据在请求体中
json_data = {
    "currentTime": "张三",
    "language": "en",
    "request_data": clientInfo
}

response = requests.post(url, json=json_data)
print(response.json())