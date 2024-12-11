from tortoise.models import Model
from tortoise import fields
from pathlib import Path
from tortoise.queryset import QuerySet
from typing import List, Dict, Any

import src.constant as constants

class UserFilesModel(Model):
    id = fields.IntField(pk=True)
    user = fields.CharField(max_length=50)
    topic = fields.TextField()
    topic_uuid = fields.UUIDField(null = True)
    file_path = fields.CharField(max_length=255)
    file_url = fields.CharField(max_length=555)
    folder_name = fields.CharField(max_length=555)

    class Meta:
        table = "files"

    @staticmethod
    async def createFilePath(**kwargs) -> str:
        try:
            # Define base directory and folder structure
            folder_name = f"{kwargs.get('user_id')}_{kwargs.get('uuid')}_{kwargs.get('topic')}"
            base_dir = Path(constants.BASE_DIR) / "media" / folder_name
            # Construct file path
            url = f"""{constants.singletonObjectDict.get("app_data",{}).get("host","localhost")}:{constants.singletonObjectDict.get("app_data",{}).get("port",8003)}/{constants.singletonObjectDict.get("app_data",{}).get("media","media")}/{folder_name}"""
            file_path = base_dir / kwargs.get("filename")
            # Ensure the path is in OS-specific format
            return str(file_path), str(url) ,str(base_dir)
        except Exception as e:
            raise Exception(f"failed due to {e}")
        
    @staticmethod
    async def getUserDocumentList(user_id : str,limit : int = 10 , order_by : bool = True , offset : int = 1):
        if order_by:
            o = "id"
        else:
            o ="-id"
        query: QuerySet = UserFilesModel.filter(user=user_id).order_by(o)
        total_count = await query.count()
        documents: List[UserFilesModel] = await query.offset(offset).limit(limit)
        return {
            "total_count": total_count,
            "documents": [doc.to_dict() for doc in documents]
        }
    

    # Helper functions 
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the model instance to a dictionary.
        """
        return {
            "id": self.id,
            "user": self.user,
            "topic": self.topic,
            "file_path": self.file_path
        }

class UserFileEmbedding(Model):
    topic_uuid = fields.UUIDField()
    embedding = fields.JSONField()

    class Meta:
        table = "files_embeddings"
