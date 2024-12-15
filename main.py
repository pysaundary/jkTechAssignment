import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.staticfiles import StaticFiles

from src.utilities.logger import InternalLoggers
from src.utilities.jsonHelper import readJsonData
from src.utilities.osHelper import getOsName,getCurrentDir,joinDirectory
from src.communication.postgres import TortoiseConnector
from src.controller.controller import llmRouter
import src.constant as constants
from src.utilities.transformers.autobot import Bumblebee
constants.BASE_DIR = getCurrentDir()
constants.internalLoggers = InternalLoggers.init_loggers(base_dir=constants.BASE_DIR)

dbConnector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await dbConnector.connect()
    yield
    await dbConnector.disconnect()

app = None

def startTasks():
    global dbConnector, app 
    logger = constants.internalLoggers.get("app",None)
    try:
        configFilePath = joinDirectory("config/config.json")
        isJsonLoaded,configData = readJsonData(configFilePath)
        if isJsonLoaded:
            constants.singletonObjectDict["app_version"] = configData.get("app_version","undefine")
            constants.singletonObjectDict["communication"] = configData.get("communication",None)
            constants.singletonObjectDict["app_data"] = configData.get("app",None)
            constants.singletonObjectDict["logger"] = configData.get("logger",None)
            constants.singletonObjectDict["transformer"] = configData.get("transformer",None)
            dbConnectorKwagrs = {
                "communication":constants.singletonObjectDict.get("communication",{}),
                "logger":constants.internalLoggers.get("postgres",None)
            }
            dbConnector = TortoiseConnector(**dbConnectorKwagrs)
            if logger:
                logger.info(f"App Started \n \t \t \t \t \t \t App version : {constants.singletonObjectDict['app_version']}")
            # Add models 
            TortoiseConnector.addModelName("src.models.models")
            Bumblebee.createHuggingFace(
                modelName = constants.singletonObjectDict["transformer"]["model_name"],
                device = constants.singletonObjectDict["transformer"]["device"],
                normalizeEmbeddings = constants.singletonObjectDict["transformer"]["normalize_embeddings"]
            )
            app = FastAPI(lifespan=lifespan)
            app.include_router(
                llmRouter,
                prefix="/llm-api",
                tags=["llm-apis"]
            )
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            app.mount("/media", StaticFiles(directory=constants.singletonObjectDict.get("app_data",{}).get("media","media")), name="media")
            
    except Exception as e:
        if logger:
            logger.error(f"App fai due to {e}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        startTasks()
        if app:
            constants.internalLoggers.get("app").info("App is about to start")
            host = constants.singletonObjectDict.get("app_data").get("host","localhost")
            port = int(constants.singletonObjectDict.get("app_data").get("port",8003))
            uvicorn.run(
                app, 
                host=host, 
                port=port, 
                reload=False
                )
            # delete before gc (no need but i will do)
            del port,host
        else:
            constants.internalLoggers.get("app").error("Application failed to start.")
    except Exception as e:
        constants.internalLoggers.get("app").error(f"Application failed to start due to {e}")