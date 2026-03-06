import yaml
import os
from fastapi import FastAPI
from routers.query import query as query_router 
from internal.config import config as config
import uvicorn



app = FastAPI(
    title= f"API FastAPI wlkg",
    description="API FastAPI wlkg",
    version="0.1",
    openapi_tags=[
        {  
            "name": "wlkg",
        }
    ]
)

app.include_router(query_router)

from fastapi.responses import FileResponse
@app.get("/download")
async def download_file():
    file_path = "C:/Users/Flavi/wlkg/progetto finale/wlkg/"
    return FileResponse(
        path=file_path, 
        filename="docs.pdf", 
        media_type='application/octet-stream'
    )

@app.get("/")
async def root():
    return {"message": f"Benvenuto nell'API di {config.name}!"}


@app.get("/data")
async def root():

    return {
        "app_name": config.name,
        "endpoint": config.endpoint,
        "namespace_left": config.namespace.left.entitytype,  
        "namespace_right": config.namespace.right["entità1"].label,
        "prefix": config.prefix["urw"]
    }



@app.get("/info_entities")
async def root():
    entities = {
        key: {
            "color": value.color,
            "label": value.label,
            "type": value.type,
            "info": value.info
        }
        for key, value in config.namespace.entities_type.items()
    }

    return {"entities": entities}


if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000)
