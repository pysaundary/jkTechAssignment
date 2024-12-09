import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from src.utilities.jsonHelper import readJsonData
from src.utilities.logger import InternalLoggers
from src.utilities.osHelper import getOsName,getCurrentDir,joinDirectory
from src.communication.postgres import TortoiseConnector
from src.controller.controller import llmRouter

BASE_DIR = getCurrentDir()
singletonObjectDict : dict = {}
internalLoggers = InternalLoggers.init_loggers(base_dir=BASE_DIR)

dbConnector = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await dbConnector.connect()
    yield
    await dbConnector.disconnect()

app = None

def startTasks():
    global dbConnector, app ,internalLoggers
    logger = internalLoggers.get("app",None)
    try:
        configFilePath = joinDirectory("config/config.json")
        isJsonLoaded,configData = readJsonData(configFilePath)
        if isJsonLoaded:
            singletonObjectDict["app_version"] = configData.get("app_version","undefine")
            singletonObjectDict["communication"] = configData.get("communication",None)
            singletonObjectDict["app_data"] = configData.get("app",None)
            singletonObjectDict["logger"] = configData.get("logger",None)
            dbConnectorKwagrs = {
                "communication":singletonObjectDict.get("communication",{}),
                "logger":internalLoggers.get("postgres",None)
            }
            dbConnector = TortoiseConnector(**dbConnectorKwagrs)
            if logger:
                logger.info(f"App Started \n \t \t \t \t \t \t App version : {singletonObjectDict['app_version']}")
            # Add models 
            TortoiseConnector.addModelName("src.models.models")
            app = FastAPI(lifespan=lifespan)
            app.include_router(
                llmRouter,
                prefix="/llm-api",
                tags=["llm-apis"]
            )
            
    except Exception as e:
        if logger:
            logger.error(f"App fai due to {e}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    startTasks()
    if app:
        internalLoggers.get("app").info("App is about to start")
        host = singletonObjectDict.get("app_data").get("host","localhost")
        port = int(singletonObjectDict.get("app_data").get("port",8003))
        uvicorn.run(
            app, 
            host=host, 
            port=port, 
            reload=False
            )
        # delete before gc (no need but i will do)
        del port,host
    else:
        internalLoggers.get("app").error("Application failed to start.")
