import generateJson
import plotSave
import toHTML
import warnings
warnings.filterwarnings('ignore')

currentTime = '2024-11-10'

gs = generateJson.generateJson(currentTime=currentTime)
gs.main()

sf = plotSave.saveFig(jsonPath='./outputJson/out.json')
sf.main()

toHTML.main(currentTime=currentTime, json_file='./outputJson/out.json', language="en")




###############################################################################################################
# import generateJson
# import plotSave
# import toHTML
# import warnings
# warnings.filterwarnings('ignore')
# from fastapi import FastAPI
# from pydantic import BaseModel
# import uvicorn
# import pandas as pd
# import json
# from typing import Dict, Any

# # 创建FastAPI实例
# app = FastAPI()

# # 创建API端点
# @app.post("/process/")
# async def process_data(json_data: Dict[str, Any]):
#     # 获取参数和JSON数据
#     # print(f"currentTime: {currentTime}")
#     # print(f"language: {language}")
#     # print(f"JSON数据: {request_data.data}")
#     currentTime = json_data["currentTime"]
#     language = json_data["language"]
#     # clientInfo = pd.DataFrame(json_data["clientInfo"])
#     clientInfo = json.loads(json_data["clientInfo"])
#     clientInfo = pd.DataFrame(clientInfo)
#     clientInfo.to_json("./inputdata/clientInfo.json", orient="records", force_ascii=False, indent=4)

#     gs = generateJson.generateJson(currentTime=currentTime)
#     gs.main()

#     sf = plotSave.saveFig(jsonPath='./outputJson/out.json')
#     sf.main()

#     toHTML.main(currentTime=currentTime, json_file='./outputJson/out.json', language="en")
#     return {"status": "success"}

# if __name__ == "__main__":
#     # 启动服务器
#     uvicorn.run(app, host="127.0.0.1", port=8000)

###############################################################################################################
### testing
# import requests
# import pandas as pd
# import json

# # URL中的路径参数: 
# # - user_id = "12345"
# # - action = "update"
# url = "http://127.0.0.1:8000/process"
# # ?currentTime=2024-11-10&language=en"
# clientInfo = pd.read_json("./inputData/clientInfo.json")
# clientInfo = clientInfo.to_dict('records')
# clientInfo = json.dumps(clientInfo, ensure_ascii=False)

# # currentTime = "2024-11-10"
# # language = "en"

# json_data = {
#     "currentTime": "2024-11-10",
#     "language": "en",
#     "clientInfo": clientInfo
# }

# response = requests.post(url, json=json_data)
# print(response.json())