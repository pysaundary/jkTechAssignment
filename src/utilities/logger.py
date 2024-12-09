import logging.handlers
import sys
import os
import logging

class PyLogger:
    def __init__(self,logger_name : str ,log_file_name : str ,log_dir_name : str = "./logs",stdout_print : bool = True, log_size_mb : int = 50 , max_log_files : int = 30):
        self.logger_name = logger_name
        self.log_file_name = log_file_name
        self.log_dir_name = log_dir_name
        self.log_instance = None
        self.STDOUT_PRINT = stdout_print
        self.log_size_mb = log_size_mb
        self.max_log_files = max_log_files

    def createLogger(self):
        self.addCustomLevelName()
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s: [%(levelname)s] [%(threadName)s] [%(filename)s]"
            "[%(funcName)s-%(lineno)d] %(message)s"
        )
        if not logger.handlers:
            if not os.path.exists(self.log_dir_name):
                os.makedirs(self.log_dir_name)
            handler = logging.handlers.RotatingFileHandler(
                os.path.join(self.log_dir_name,self.log_file_name),
                maxBytes=(1048576*self.log_size_mb),
                backupCount=self.max_log_files
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            if self.STDOUT_PRINT:
                logger.addHandler(logging.StreamHandler(stream=sys.stdout))

        self.log_instance = logger
        return self.log_instance
    
    def getInstance(self):
        if not self.log_instance:
            self.createLogger()
        return self.log_instance
    
    def addCustomLevelName(self):
        logging.addLevelName(logging.DEBUG,"DBG")
        logging.addLevelName(logging.INFO,"INF")
        logging.addLevelName(logging.WARNING,"WRN")
        logging.addLevelName(logging.ERROR,"ERR")
        logging.addLevelName(logging.CRITICAL,"CRI")

class InternalLoggers:
    _instances = {}

    @classmethod
    def init_loggers(cls, base_dir=None):
        loggers = {}
        if not base_dir:
            for instance_dict in cls._instances.values():
                for instance in instance_dict.values():
                    if instance:
                        return instance
            raise ValueError("No existing instance found for any base dir")   
        if base_dir not in cls._instances:
            cls._instances[base_dir] = {}
            loggers = cls._instances[base_dir]
            
            loggers["app"] = PyLogger(
                "app_logger",
                "app.log",
                f"{base_dir}/logs/app",
                stdout_print = True 
            ).getInstance()

            loggers["postgres"] = PyLogger(
                "postgres",
                "postgres.log",
                f"{base_dir}/logs/postgres",
                stdout_print = True 
            ).getInstance()

            loggers["apis_logs"] = PyLogger(
                "api_logger",
                "api.log",
                f"{base_dir}/logs/api",
                stdout_print = True 
            ).getInstance()

        return loggers