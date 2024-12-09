import json
from src.utilities.logger import PyLogger
import traceback

def readJsonData(filePath : str,logger:PyLogger = None)->tuple:
    try:
        with open(filePath,'r') as file:
            data = json.load(file)
        return True,data
    except Exception as e: 
        if PyLogger:
            logger.error(f"failed to read json file from {filePath} due to {e}")
            logger.error(traceback.format_exc())
            return False,{}
        