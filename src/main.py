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


# import uvicorn
# from fastapi import FastAPI, UploadFile, File
# from fastapi.responses import JSONResponse, HTMLResponse
# import json
# import generateJson
# import plotSave
# import toHTML
# import warnings
# from datetime import datetime
# from typing import Optional

# warnings.filterwarnings('ignore')

# app = FastAPI()

# @app.post("/process")
# async def process_data(current_time: Optional[str] = None, language: str = "en"):
#     try:
#         # Use provided time or default to current time
#         if not current_time:
#             current_time = datetime.now().strftime('%Y-%m-%d')

#         # Generate JSON
#         gs = generateJson.generateJson(currentTime=current_time)
#         gs.main()

#         # Save figures
#         sf = plotSave.saveFig(jsonPath='./outputJson/out.json')
#         sf.main()

#         # Generate HTML
#         html_content = toHTML.main(
#             currentTime=current_time, 
#             json_file='./outputJson/out.json', 
#             language=language
#         )

#         return HTMLResponse(content=html_content, media_type="text/html")

#     except Exception as e:
#         return JSONResponse(
#             content={"error": f"Processing failed: {str(e)}"}, 
#             status_code=500
#         )

# @app.post("/upload-and-process")
# async def upload_and_process(
#     file: UploadFile = File(...),
#     current_time: Optional[str] = None,
#     language: str = "en"
# ):
#     try:
#         if not file.filename.endswith('.json'):
#             return JSONResponse(
#                 content={"error": "Please upload a JSON file"}, 
#                 status_code=400
#             )

#         # Save uploaded file
#         contents = await file.read()
#         with open('./outputJson/out.json', 'wb') as f:
#             f.write(contents)

#         # Use provided time or default to current time
#         if not current_time:
#             current_time = datetime.now().strftime('%Y-%m-%d')

#         # Save figures
#         sf = plotSave.saveFig(jsonPath='./outputJson/out.json')
#         sf.main()

#         # Generate HTML
#         html_content = toHTML.main(
#             currentTime=current_time, 
#             json_file='./outputJson/out.json', 
#             language=language
#         )

#         return HTMLResponse(content=html_content, media_type="text/html")

#     except Exception as e:
#         return JSONResponse(
#             content={"error": f"Processing failed: {str(e)}"}, 
#             status_code=500
#         )

# if __name__ == "__main__":
#     config = uvicorn.Config("main:app", host='0.0.0.0', port=8080)
#     server = uvicorn.Server(config)
#     server.run()