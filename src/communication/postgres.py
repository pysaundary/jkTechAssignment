from tortoise import Tortoise, run_async
from tortoise.transactions import in_transaction


class TortoiseConnector:
    _instance = None
    _models = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TortoiseConnector, cls).__new__(cls)
        return cls._instance

    def __init__(self, **kwargs):
        if not hasattr(self, 'initialized'):
            self.env = kwargs.get("communication", {}).get("postgres",{})
            self.userName = self.env.get("user", "postgres")
            self.userPassword = self.env.get("password", "10101990")
            self.dbName = self.env.get("db_name", "open_expenses")
            self.dbPort = self.env.get("port", "5432")
            self.dbHost = self.env.get("host", "localhost")
            self.logger = kwargs.get("logger",None)
            self.isConnected = False
            self.initialized = True

    @classmethod
    def addModelName(cls,name:str):
        TortoiseConnector._models.append(name)

    async def connect(self):
        if self.logger:
            self.logger.info("trying to  connect with postgres db")
        if not self.isConnected:
            db_url = f"postgres://{self.userName}:{self.userPassword}@{self.dbHost}:{self.dbPort}/{self.dbName}"
            await Tortoise.init(
                db_url=db_url,
                modules={"models": TortoiseConnector._models},  # Replace with your actual models package
            )
            await Tortoise.generate_schemas()
            self.isConnected = True
            if self.logger:
                self.logger.info(f"Connection with Postgres DB {self.dbName} is successfully done")

    async def disconnect(self):
        if self.logger:
            self.logger.info("trying to disconnect with postgres db")
        if self.isConnected:
            await Tortoise.close_connections()
            self.isConnected = False
            if self.logger:
                self.logger.info(f"Disconnection with MySQL DB {self.dbName} is successfully done")

    def get_transaction(self):
        """
        Returns an in_transaction context manager for transactional operations.
        """
        return in_transaction()
