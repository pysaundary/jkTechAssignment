import os
import platform
from pathlib import Path

def getOsName()->bool:
    """This function will return True for linux (basically if linux uvloop will be event loop) """
    osName = platform.system()
    if osName == "Windos":
        return False
    elif osName == "Linux":
        return True
    else:
        return False

def getCurrentDir():
    return os.getcwd()    

def joinDirectory(joinPath : str ,rootDir : str = getCurrentDir() )->str:
    return os.path.join(rootDir,joinPath)
