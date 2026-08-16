from pymongo import MongoClient

class MongoDBConnection:
    def __init__(self):
        self.client = None
        self.db = None

    def connect(self, uri: str, db_name: str):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def disconnect(self):
        if self.client:
            self.client.close()

db_manager = MongoDBConnection()
